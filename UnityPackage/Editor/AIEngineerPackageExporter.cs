using System.IO;
using UnityEditor;
using UnityEngine;

namespace AIEngineer.Editor
{
    /// <summary>Exports the reviewed Control Center, account-provider safeguards, apply handlers, acceptance checks, docs, and portable backend as one importable Unity package.</summary>
    public static class AIEngineerPackageExporter
    {
        private const string PackageRoot = "Assets/AIEngineer";
        private const string PendingExportPath = PackageRoot + "/ExportCompletePackage.txt";
        private const string PackageFileName = "AIEngineer-Complete.unitypackage";

        [MenuItem("AI Engineer/Package/Export Complete Unity Package")]
        public static void ExportCompletePackage()
        {
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
            var output = Path.Combine(projectRoot, PackageFileName);
            AssetDatabase.ExportPackage(PackageRoot, output, ExportPackageOptions.Recurse | ExportPackageOptions.IncludeDependencies);
            Debug.Log("AI Engineer complete Unity package exported: " + output);
        }

        [InitializeOnLoadMethod]
        private static void ExportPendingPackageAfterReload()
        {
            EditorApplication.delayCall += () =>
            {
                // Unity's process directory is not guaranteed to be the project root.
                // Resolve the marker from Application.dataPath so a request written
                // through the package junction is detected reliably.
                var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
                var pendingAbsolutePath = Path.Combine(projectRoot, PendingExportPath);
                if (!File.Exists(pendingAbsolutePath)) return;
                AssetDatabase.DeleteAsset(PendingExportPath);
                AssetDatabase.SaveAssets();
                ExportCompletePackage();
            };
        }
    }
}
