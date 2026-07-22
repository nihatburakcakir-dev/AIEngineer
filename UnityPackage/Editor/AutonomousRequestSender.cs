using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using AIEngineer.Scene;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Networking;

namespace AIEngineer.Editor.Autonomy
{
    public static class AutonomousRequestSender
    {
        private const string BaseUrl = "http://127.0.0.1:8080";

        public static async Task<AutonomousChangeSet> Plan(string prompt, string imagePath, string modelMode)
        {
            var importedReference = PrepareReferenceImage(imagePath);
            var request = new AutonomousPlanRequest
            {
                prompt = prompt,
                projectPath = Directory.GetParent(Application.dataPath)?.FullName,
                activeScene = EditorSceneManager.GetActiveScene().path,
                imagePath = importedReference,
                modelMode = modelMode,
                visionMode = modelMode,
                targetOrientation = Screen.width >= Screen.height ? "landscape" : "portrait",
                language = AIEngineerLocalization.Current == AIEngineerLanguage.Turkish ? "Turkish" : "English",
                selectedAssets = Selection.objects.Select(AssetDatabase.GetAssetPath).Where(path => !string.IsNullOrWhiteSpace(path)).Distinct().ToArray(),
                objects = SceneExporter.Export().ToArray(),
                project = ProjectSnapshot(),
            };
            return await Send<AutonomousPlanRequest>("/v1/plan", request);
        }

        // A user-selected reference can live outside the Unity project. Import a
        // private project copy before planning so generated prefabs can safely keep
        // a serializable Texture reference instead of a machine-specific file path.
        private static string PrepareReferenceImage(string imagePath)
        {
            if (string.IsNullOrWhiteSpace(imagePath)) return string.Empty;
            var normalized = imagePath.Replace('\\', '/');
            if (normalized.StartsWith("Assets/", StringComparison.Ordinal)) return normalized;
            if (!File.Exists(imagePath)) throw new FileNotFoundException("Reference image was not found.", imagePath);
            var extension = Path.GetExtension(imagePath).ToLowerInvariant();
            if (extension != ".png" && extension != ".jpg" && extension != ".jpeg" && extension != ".webp")
                throw new InvalidDataException("Reference image must be PNG, JPG, JPEG or WEBP.");
            const string folder = "Assets/AIEngineerGenerated/ReferenceImages";
            var absoluteFolder = Path.Combine(Application.dataPath, "AIEngineerGenerated", "ReferenceImages");
            Directory.CreateDirectory(absoluteFolder);
            var assetPath = AssetDatabase.GenerateUniqueAssetPath(folder + "/" + Path.GetFileName(imagePath));
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
            File.Copy(imagePath, Path.Combine(projectRoot, assetPath), false);
            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceSynchronousImport);
            return assetPath;
        }

        public static async Task<AutonomousChangeSet> Repair(
            string prompt, string imagePath, string modelMode, AutonomousChangeSet previous, string[] diagnostics, int attempt)
        {
            var request = new AutonomousRepairRequest
            {
                prompt = prompt,
                projectPath = Directory.GetParent(Application.dataPath)?.FullName,
                activeScene = EditorSceneManager.GetActiveScene().path,
                imagePath = imagePath ?? string.Empty,
                modelMode = modelMode,
                visionMode = modelMode,
                targetOrientation = Screen.width >= Screen.height ? "landscape" : "portrait",
                language = AIEngineerLocalization.Current == AIEngineerLanguage.Turkish ? "Turkish" : "English",
                selectedAssets = Selection.objects.Select(AssetDatabase.GetAssetPath).Where(path => !string.IsNullOrWhiteSpace(path)).Distinct().ToArray(),
                objects = SceneExporter.Export().ToArray(),
                project = ProjectSnapshot(),
                changeSet = previous,
                diagnostics = diagnostics ?? Array.Empty<string>(),
                attempt = attempt,
            };
            return await Send<AutonomousRepairRequest>("/v1/repair", request);
        }

        private static ProjectModel ProjectSnapshot()
        {
            return new ProjectModel
            {
                prefabs = ProjectExporter.GetPrefabs(), materials = ProjectExporter.GetMaterials(),
                textures = ProjectExporter.GetTextures(), audio = ProjectExporter.GetAudio(),
                scripts = ProjectExporter.GetScripts(), animations = ProjectExporter.GetAnimations(),
                scenes = ProjectExporter.GetScenes(),
            };
        }

        private static async Task<AutonomousChangeSet> Send<T>(string endpoint, T payload)
        {
            if (!ServerManager.IsRunning)
            {
                ServerManager.Start();
                await Task.Delay(900);
            }
            var json = JsonUtility.ToJson(payload, false);
            using var request = new UnityWebRequest(BaseUrl + endpoint, "POST");
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            request.timeout = 420;
            var operation = request.SendWebRequest();
            while (!operation.isDone) await Task.Yield();
            var body = request.downloadHandler?.text ?? string.Empty;
            if (request.result != UnityWebRequest.Result.Success)
                throw new InvalidOperationException($"Backend HTTP {request.responseCode}: {body}\n{request.error}");
            var result = JsonUtility.FromJson<AutonomousChangeSet>(body);
            if (result == null || !result.IsValid)
                throw new InvalidDataException("Backend returned an invalid autonomous change set: " + body);
            return result;
        }
    }
}
