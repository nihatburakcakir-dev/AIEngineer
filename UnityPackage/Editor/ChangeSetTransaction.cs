using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace AIEngineer.Editor.Autonomy
{
    [Serializable]
    internal sealed class TransactionRecord
    {
        public string assetPath;
        public bool existed;
        public string backupFile;
        public bool metaExisted;
        public string metaBackupFile;
    }

    [Serializable]
    internal sealed class TransactionManifest
    {
        public string id;
        public string requestId;
        public string status;
        public string activeScene;
        public string createdAt;
        public TransactionRecord[] records;
    }

    internal sealed class ChangeSetTransaction
    {
        private readonly string projectRoot;
        private readonly string transactionRoot;
        private readonly string manifestPath;
        private readonly List<TransactionRecord> records;
        private readonly TransactionManifest manifest;

        public string Id => manifest.id;

        private ChangeSetTransaction(TransactionManifest source)
        {
            projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
            transactionRoot = Path.Combine(projectRoot, "Library", "AIEngineer", "Transactions", source.id);
            manifestPath = Path.Combine(transactionRoot, "manifest.json");
            manifest = source;
            records = source.records?.ToList() ?? new List<TransactionRecord>();
        }

        public static ChangeSetTransaction Begin(string requestId)
        {
            var id = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N").Substring(0, 8);
            var source = new TransactionManifest
            {
                id = id,
                requestId = requestId,
                status = "active",
                // Package-owned sample scenes are deliberately not rollback targets.
                // Autonomous jobs clone those scenes into AIEngineerGenerated before editing.
                activeScene = IsProtectedPackagePath(EditorSceneManager.GetActiveScene().path)
                    ? string.Empty
                    : EditorSceneManager.GetActiveScene().path,
                createdAt = DateTime.UtcNow.ToString("O"),
                records = Array.Empty<TransactionRecord>(),
            };
            var transaction = new ChangeSetTransaction(source);
            Directory.CreateDirectory(transaction.transactionRoot);
            transaction.Save();
            return transaction;
        }

        public static ChangeSetTransaction Load(string id)
        {
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
            var path = Path.Combine(projectRoot, "Library", "AIEngineer", "Transactions", id, "manifest.json");
            if (!File.Exists(path)) throw new FileNotFoundException("Transaction manifest was not found.", path);
            return new ChangeSetTransaction(JsonUtility.FromJson<TransactionManifest>(File.ReadAllText(path)));
        }

        public void Snapshot(string assetPath)
        {
            if (string.IsNullOrWhiteSpace(assetPath)) return;
            assetPath = NormalizeAssetPath(assetPath);
            if (records.Any(record => string.Equals(record.assetPath, assetPath, StringComparison.OrdinalIgnoreCase))) return;
            var fullPath = FullPath(assetPath);
            if (Directory.Exists(fullPath))
            {
                foreach (var file in Directory.GetFiles(fullPath, "*", SearchOption.AllDirectories))
                {
                    if (file.EndsWith(".meta", StringComparison.OrdinalIgnoreCase)) continue;
                    Snapshot(Path.GetRelativePath(projectRoot, file).Replace('\\', '/'));
                }
                return;
            }
            var index = records.Count.ToString("D4");
            var record = new TransactionRecord
            {
                assetPath = assetPath,
                existed = File.Exists(fullPath),
                backupFile = Path.Combine(transactionRoot, index + ".data"),
                metaExisted = File.Exists(fullPath + ".meta"),
                metaBackupFile = Path.Combine(transactionRoot, index + ".meta"),
            };
            if (record.existed) File.Copy(fullPath, record.backupFile, true);
            if (record.metaExisted) File.Copy(fullPath + ".meta", record.metaBackupFile, true);
            records.Add(record);
            Save();
        }

        public void SnapshotActiveScene()
        {
            var scene = EditorSceneManager.GetActiveScene();
            var scenePath = (scene.path ?? string.Empty).Replace('\\', '/');
            if (string.IsNullOrWhiteSpace(scenePath)) return;
            if (!IsProtectedPackagePath(scenePath))
            {
                Snapshot(scenePath);
                return;
            }

            // Effects, components, game objects and UI all share this guard.  The
            // package stays immutable while the user receives an editable copy.
            var sceneName = Path.GetFileNameWithoutExtension(scenePath);
            if (string.IsNullOrWhiteSpace(sceneName)) sceneName = "GeneratedGame";
            var generatedPath = "Assets/AIEngineerGenerated/Games/" + sceneName + "/" + sceneName + ".unity";
            Snapshot(generatedPath);
            Directory.CreateDirectory(Path.GetDirectoryName(FullPath(generatedPath)) ?? projectRoot);
            if (!EditorSceneManager.SaveScene(scene, generatedPath, true))
                throw new InvalidOperationException("Protected sample scene could not be copied to: " + generatedPath);
            EditorSceneManager.OpenScene(generatedPath, OpenSceneMode.Single);
            Debug.Log("[AI Autonomous] Protected sample scene copied to editable game output: " + generatedPath);
        }

        public void Complete()
        {
            manifest.status = "complete";
            Save();
        }

        public void MarkRolledBack()
        {
            manifest.status = "rolled_back";
            Save();
        }

        public bool Rollback(out string message, bool refresh = true)
        {
            try
            {
                foreach (var record in records.AsEnumerable().Reverse()) Restore(record);
                if (refresh)
                {
                    AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
                    if (!string.IsNullOrWhiteSpace(manifest.activeScene) && !IsProtectedPackagePath(manifest.activeScene) && File.Exists(FullPath(manifest.activeScene)))
                        EditorSceneManager.OpenScene(manifest.activeScene, OpenSceneMode.Single);
                }
                MarkRolledBack();
                message = "Transaction rolled back: " + Id;
                return true;
            }
            catch (Exception error)
            {
                message = "Rollback failed: " + error.Message;
                return false;
            }
        }

        public string FullPath(string assetPath)
        {
            assetPath = NormalizeAssetPath(assetPath);
            var full = Path.GetFullPath(Path.Combine(projectRoot, assetPath.Replace('/', Path.DirectorySeparatorChar)));
            var allowedRoot = Path.GetFullPath(Path.Combine(projectRoot, "Assets")) + Path.DirectorySeparatorChar;
            if (!full.StartsWith(allowedRoot, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Path escapes Unity Assets: " + assetPath);
            return full;
        }

        public static string NormalizeAssetPath(string assetPath)
        {
            var path = (assetPath ?? string.Empty).Trim().Replace('\\', '/');
            if (!path.StartsWith("Assets/", StringComparison.Ordinal) || path.Contains("../") || Path.IsPathRooted(path))
                throw new InvalidOperationException("Only project-relative Assets paths are allowed: " + assetPath);
            if (IsProtectedPackagePath(path))
                throw new InvalidOperationException("Autonomous plans cannot modify the AI Engineer package itself: " + assetPath);
            return path;
        }

        private static bool IsProtectedPackagePath(string assetPath)
        {
            return (assetPath ?? string.Empty).Replace('\\', '/')
                .StartsWith("Assets/AIEngineer/", StringComparison.OrdinalIgnoreCase);
        }

        private void Restore(TransactionRecord record)
        {
            var target = FullPath(record.assetPath);
            if (record.existed)
            {
                Directory.CreateDirectory(Path.GetDirectoryName(target) ?? projectRoot);
                File.Copy(record.backupFile, target, true);
            }
            else if (File.Exists(target)) File.Delete(target);
            else if (Directory.Exists(target)) Directory.Delete(target, true);

            if (record.metaExisted)
            {
                Directory.CreateDirectory(Path.GetDirectoryName(target) ?? projectRoot);
                File.Copy(record.metaBackupFile, target + ".meta", true);
            }
            else if (File.Exists(target + ".meta")) File.Delete(target + ".meta");
        }

        private void Save()
        {
            manifest.records = records.ToArray();
            Directory.CreateDirectory(transactionRoot);
            File.WriteAllText(manifestPath, JsonUtility.ToJson(manifest, true));
        }
    }
}
