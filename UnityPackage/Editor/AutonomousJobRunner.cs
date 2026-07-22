using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UnityEditor;
using UnityEditor.Compilation;
using UnityEngine;

namespace AIEngineer.Editor.Autonomy
{
    [Serializable]
    internal sealed class StringList
    {
        public string[] items;
    }

    [Serializable]
    public sealed class AutonomousJobState
    {
        public string prompt;
        public string imagePath;
        public string modelMode;
        public AutonomousChangeSet changeSet;
        public int attempt;
        public int maxAttempts;
        public string stage;
        public string transactionId;
        public string status;
        public string startedAt;
        public string updatedAt;
        public string resumeAfterUtc;
        public string[] diagnostics;

        public bool IsBusy => stage is "applying_files" or "waiting_compile" or "applying_unity" or "waiting_play" or "repairing";
    }

    // Pending editor commands are intentionally consumed only after a domain reload; scoped repair acceptance.
    [InitializeOnLoad]
    public static class AutonomousJobRunner
    {
        private static readonly string ProjectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
        private static readonly string JobRoot = Path.Combine(ProjectRoot, "Library", "AIEngineer", "Jobs");
        private static readonly string StatePath = Path.Combine(JobRoot, "current.json");
        private static readonly string CompilerErrorsPath = Path.Combine(JobRoot, "compiler-errors.json");
        private const string PendingAcceptancePath = "Assets/AIEngineer/AutonomousAcceptanceRequest.json";
        private const string PendingRollbackPath = "Assets/AIEngineer/RollbackAutonomousAcceptance.request";
        private static bool resuming;

        public static event Action StateChanged;

        static AutonomousJobRunner()
        {
            Directory.CreateDirectory(JobRoot);
            CompilationPipeline.assemblyCompilationFinished -= OnAssemblyCompilationFinished;
            CompilationPipeline.assemblyCompilationFinished += OnAssemblyCompilationFinished;
            EditorApplication.playModeStateChanged -= OnPlayModeStateChanged;
            EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
            Application.logMessageReceived -= OnRuntimeLog;
            Application.logMessageReceived += OnRuntimeLog;
            EditorApplication.delayCall += ConsumePendingEditorCommands;
            EditorApplication.delayCall += ScheduleResume;
        }

        public static AutonomousJobState Current => LoadState();
        public static bool IsBusy => Current?.IsBusy == true;
        public static string LastStatus => Current?.status ?? AIEngineerLocalization.Text("Henuz otonom is yok.", "No autonomous job yet.");

        [Serializable]
        private sealed class PendingAcceptanceRequest
        {
            public string prompt;
            public string imagePath;
            public string modelMode;
            public int maxAttempts = 3;
            public AutonomousChangeSet changeSet;
        }

        public static void Start(string prompt, string imagePath, string modelMode, AutonomousChangeSet changeSet, int maxAttempts = 3)
        {
            if (changeSet == null || !changeSet.IsValid) throw new ArgumentException("A valid change set is required.");
            if (IsBusy) throw new InvalidOperationException("Another autonomous job is already running.");
            var state = new AutonomousJobState
            {
                prompt = prompt,
                imagePath = imagePath ?? string.Empty,
                modelMode = string.IsNullOrWhiteSpace(modelMode) ? "local" : modelMode,
                changeSet = changeSet,
                attempt = 1,
                maxAttempts = Mathf.Clamp(maxAttempts, 1, 3),
                stage = "applying_files",
                status = AIEngineerLocalization.Text("Yedek aliniyor ve dosya islemleri uygulaniyor.", "Creating a transaction and applying file operations."),
                startedAt = DateTime.UtcNow.ToString("O"),
                diagnostics = Array.Empty<string>(),
            };
            ApplyAttempt(state);
        }

        public static bool RollbackLast(out string message)
        {
            var state = LoadState();
            if (state == null || string.IsNullOrWhiteSpace(state.transactionId))
            {
                message = AIEngineerLocalization.Text("Geri alinacak islem bulunamadi.", "No transaction is available to roll back.");
                return false;
            }
            if (state.IsBusy)
            {
                message = AIEngineerLocalization.Text("Islem devam ederken elle geri alinamaz.", "A running job cannot be manually rolled back.");
                return false;
            }
            var success = ChangeSetTransaction.Load(state.transactionId).Rollback(out message);
            if (success)
            {
                state.stage = "rolled_back";
                state.status = message;
                SaveState(state);
            }
            return success;
        }

        private static void ConsumePendingEditorCommands()
        {
            if (File.Exists(PendingRollbackPath))
            {
                AssetDatabase.DeleteAsset(PendingRollbackPath);
                AssetDatabase.SaveAssets();
                if (RollbackLast(out var rollbackMessage)) Debug.Log("[AI Autonomous Acceptance] ROLLBACK PASS: " + rollbackMessage);
                else Debug.LogError("[AI Autonomous Acceptance] ROLLBACK FAIL: " + rollbackMessage);
            }
            if (!File.Exists(PendingAcceptancePath)) return;
            var json = File.ReadAllText(PendingAcceptancePath);
            AssetDatabase.DeleteAsset(PendingAcceptancePath);
            AssetDatabase.SaveAssets();
            var request = JsonUtility.FromJson<PendingAcceptanceRequest>(json);
            if (request?.changeSet == null)
            {
                Debug.LogError("[AI Autonomous Acceptance] Invalid pending change set.");
                return;
            }
            Start(request.prompt, request.imagePath, request.modelMode, request.changeSet, request.maxAttempts);
        }

        private static void ApplyAttempt(AutonomousJobState state)
        {
            try
            {
                var transaction = ChangeSetTransaction.Begin(state.changeSet.requestId);
                state.transactionId = transaction.Id;
                state.stage = "applying_files";
                state.status = AIEngineerLocalization.Text($"Otonom deneme {state.attempt}/{state.maxAttempts}: dosya islemleri.", $"Autonomous attempt {state.attempt}/{state.maxAttempts}: applying file operations.");
                ClearCompilerErrors();
                SaveState(state);
                AutonomousChangeSetExecutor.ApplyFilePhase(state.changeSet, transaction);
                state.stage = "waiting_compile";
                state.status = AIEngineerLocalization.Text("Unity derlemesi bekleniyor.", "Waiting for Unity compilation.");
                state.resumeAfterUtc = DateTime.UtcNow.AddSeconds(2).ToString("O");
                SaveState(state);
                AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);
                ScheduleResume();
            }
            catch (Exception error)
            {
                FailAndRollback(state, "File operation failed: " + error.Message);
            }
        }

        private static void ScheduleResume()
        {
            EditorApplication.update -= PollResume;
            EditorApplication.update += PollResume;
        }

        private static void PollResume()
        {
            var state = LoadState();
            if (state == null || state.stage != "waiting_compile")
            {
                EditorApplication.update -= PollResume;
                return;
            }
            if (EditorApplication.isCompiling || EditorApplication.isUpdating || DateTime.UtcNow < ParseDate(state.resumeAfterUtc)) return;
            EditorApplication.update -= PollResume;
            ResumeAfterCompile();
        }

        private static async void ResumeAfterCompile()
        {
            if (resuming) return;
            resuming = true;
            try
            {
                var state = LoadState();
                if (state == null || state.stage != "waiting_compile") return;
                var errors = ReadCompilerErrors();
                if (errors.Length > 0)
                {
                    await RepairOrRollback(state, errors);
                    return;
                }
                try
                {
                    state.stage = "applying_unity";
                    state.status = AIEngineerLocalization.Text("Kod derlendi; sahne, prefab ve efekt islemleri uygulaniyor.", "Code compiled; applying scene, prefab and effect operations.");
                    SaveState(state);
                    var transaction = ChangeSetTransaction.Load(state.transactionId);
                    AutonomousChangeSetExecutor.ApplyUnityPhase(state.changeSet, transaction);
                    AutonomousChangeSetExecutor.ValidateAppliedOperations(state.changeSet);
                    if (state.changeSet.validation?.playMode == true)
                    {
                        state.stage = "waiting_play";
                        state.status = AIEngineerLocalization.Text("Play Mode dogrulamasi calisiyor.", "Running Play Mode validation.");
                        state.diagnostics = Array.Empty<string>();
                        SaveState(state);
                        EditorApplication.isPlaying = true;
                    }
                    else Complete(state, transaction);
                }
                catch (Exception error)
                {
                    await RepairOrRollback(state, new[] { LocalizeDiagnostic("Unity operation failed: " + error.Message) });
                }
            }
            finally { resuming = false; }
        }

        private static async Task RepairOrRollback(AutonomousJobState state, string[] diagnostics)
        {
            state.diagnostics = diagnostics;
            if (state.attempt >= state.maxAttempts)
            {
                FailAndRollback(state, AIEngineerLocalization.Text("Azami duzeltme denemesi doldu. ", "Maximum repair attempts reached. ") + string.Join("\n", diagnostics));
                return;
            }
            try
            {
                state.stage = "repairing";
                state.status = AIEngineerLocalization.Text("Hata yerel modele geri besleniyor; duzeltme plani uretiliyor.", "Feeding diagnostics back to the local model for a repair plan.");
                SaveState(state);
                var repaired = await AutonomousRequestSender.Repair(state.prompt, state.imagePath, state.modelMode, state.changeSet, diagnostics, state.attempt + 1);
                var transaction = ChangeSetTransaction.Load(state.transactionId);
                if (!transaction.Rollback(out var rollbackMessage, false)) throw new InvalidOperationException(rollbackMessage);
                state.changeSet = repaired;
                state.attempt += 1;
                state.diagnostics = Array.Empty<string>();
                ApplyAttempt(state);
            }
            catch (Exception error)
            {
                FailAndRollback(state, LocalizeDiagnostic("Automatic repair failed: " + error.Message));
            }
        }

        private static void OnPlayModeStateChanged(PlayModeStateChange stateChange)
        {
            var state = LoadState();
            if (state == null || state.stage != "waiting_play") return;
            if (stateChange == PlayModeStateChange.EnteredPlayMode)
            {
                state.resumeAfterUtc = DateTime.UtcNow.AddSeconds(3).ToString("O");
                SaveState(state);
                EditorApplication.update -= PollPlayMode;
                EditorApplication.update += PollPlayMode;
            }
            else if (stateChange == PlayModeStateChange.EnteredEditMode)
            {
                EditorApplication.update -= PollPlayMode;
                state = LoadState();
                if (state == null || state.stage != "waiting_play") return;
                if (state.diagnostics != null && state.diagnostics.Length > 0) _ = RepairOrRollback(state, state.diagnostics);
                else Complete(state, ChangeSetTransaction.Load(state.transactionId));
            }
        }

        private static void PollPlayMode()
        {
            var state = LoadState();
            if (state == null || state.stage != "waiting_play") { EditorApplication.update -= PollPlayMode; return; }
            if (DateTime.UtcNow < ParseDate(state.resumeAfterUtc)) return;
            EditorApplication.update -= PollPlayMode;
            EditorApplication.isPlaying = false;
        }

        private static void OnRuntimeLog(string condition, string stackTrace, LogType type)
        {
            if (type != LogType.Error && type != LogType.Exception && type != LogType.Assert) return;
            var state = LoadState();
            if (state == null || state.stage != "waiting_play") return;
            var diagnostics = state.diagnostics?.ToList() ?? new List<string>();
            diagnostics.Add(condition + "\n" + stackTrace);
            state.diagnostics = diagnostics.Take(20).ToArray();
            SaveState(state);
        }

        private static void Complete(AutonomousJobState state, ChangeSetTransaction transaction)
        {
            transaction.Complete();
            state.stage = "complete";
            state.status = AIEngineerLocalization.Text(
                $"Tamamlandi. {state.attempt} denemede uygulandi, derlendi ve dogrulandi.",
                $"Complete. Applied, compiled and validated in {state.attempt} attempt(s).");
            SaveState(state);
            Debug.Log("[AI Autonomous] " + state.status);
        }

        private static void FailAndRollback(AutonomousJobState state, string reason)
        {
            var rollback = string.Empty;
            try
            {
                if (!string.IsNullOrWhiteSpace(state.transactionId)) ChangeSetTransaction.Load(state.transactionId).Rollback(out rollback);
            }
            catch (Exception error) { rollback = LocalizeDiagnostic("Rollback exception: " + error.Message); }
            state.stage = "failed";
            state.status = reason + (string.IsNullOrWhiteSpace(rollback) ? string.Empty : "\n" + rollback);
            SaveState(state);
            Debug.LogError("[AI Autonomous] " + state.status);
        }

        private static string LocalizeDiagnostic(string text)
        {
            if (AIEngineerLocalization.Current == AIEngineerLanguage.English) return text;
            return (text ?? string.Empty)
                .Replace("Unity operation failed:", "Unity işlemi başarısız oldu:")
                .Replace("Automatic repair failed:", "Otomatik onarım başarısız oldu:")
                .Replace("Rollback exception:", "Geri alma hatası:")
                .Replace("Given path is not valid:", "Verilen yol geçersiz:")
                .Replace("UI scene could not be saved:", "UI sahnesi kaydedilemedi:")
                .Replace("UI prefab could not be saved:", "UI prefabı kaydedilemedi:");
        }

        private static void OnAssemblyCompilationFinished(string assemblyPath, CompilerMessage[] messages)
        {
            var errors = messages.Where(message => message.type == CompilerMessageType.Error)
                .Select(message => $"{message.file}({message.line},{message.column}): {message.message}").ToArray();
            if (errors.Length == 0) return;
            var current = ReadCompilerErrors().Concat(errors).Distinct().Take(100).ToArray();
            Directory.CreateDirectory(JobRoot);
            File.WriteAllText(CompilerErrorsPath, JsonUtility.ToJson(new StringList { items = current }, true));
        }

        private static void ClearCompilerErrors()
        {
            Directory.CreateDirectory(JobRoot);
            if (File.Exists(CompilerErrorsPath)) File.Delete(CompilerErrorsPath);
        }

        private static string[] ReadCompilerErrors()
        {
            if (!File.Exists(CompilerErrorsPath)) return Array.Empty<string>();
            return JsonUtility.FromJson<StringList>(File.ReadAllText(CompilerErrorsPath))?.items ?? Array.Empty<string>();
        }

        private static AutonomousJobState LoadState()
        {
            try { return File.Exists(StatePath) ? JsonUtility.FromJson<AutonomousJobState>(File.ReadAllText(StatePath)) : null; }
            catch { return null; }
        }

        private static void SaveState(AutonomousJobState state)
        {
            state.updatedAt = DateTime.UtcNow.ToString("O");
            Directory.CreateDirectory(JobRoot);
            File.WriteAllText(StatePath, JsonUtility.ToJson(state, true));
            StateChanged?.Invoke();
        }

        private static DateTime ParseDate(string value)
        {
            return DateTime.TryParse(value, null, System.Globalization.DateTimeStyles.RoundtripKind, out var parsed) ? parsed : DateTime.MinValue;
        }
    }
}
