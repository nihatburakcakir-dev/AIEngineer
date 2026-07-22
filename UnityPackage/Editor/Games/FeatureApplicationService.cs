using System.Globalization;
using System.Text;
using AIEngineer.Games;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace AIEngineer.Editor.Features
{
    /// <summary>Review-and-apply handlers for explicitly supported gameplay features.</summary>
    public static class FeatureApplicationService
    {
        public const string BallPopLightning = "ball_pop_lightning";
        private const string LightningPrefabPath = "Assets/Matthew Guz/Hits Effects FREE/Prefab/Lightning Hit Blue.prefab";
        private const string PendingInstallPath = "Assets/AIEngineer/ApplyBallPopLightning.request";

        public static bool TryCreatePlan(string prompt, out string featureId, out string plan)
        {
            var normalized = Normalize(prompt);
            var hasBallEvent = normalized.Contains("top") || normalized.Contains("marble") || normalized.Contains("ball");
            var hasPopEvent = normalized.Contains("patla") || normalized.Contains("esles") || normalized.Contains("match") || normalized.Contains("pop");
            var hasLightning = normalized.Contains("yildirim") || normalized.Contains("simsek") || normalized.Contains("lightning");
            if (!hasBallEvent || !hasPopEvent || !hasLightning)
            {
                featureId = null;
                plan = null;
                return false;
            }

            featureId = BallPopLightning;
            plan = AIEngineerLocalization.Text(
                "UYGULANABILIR PLAN\n\n1. Aktif sahneye Ball Pop Lightning Observer ekle.\n2. Mevcut renkli top patlama efektlerini olay kaynagi olarak izle.\n3. Lightning Hit Blue prefabini patlama noktasinin 5.5 birim ustunde olustur.\n4. Yildirimi 0.18 saniyede yukaridan patlama noktasina indir.\n5. Efekti 2 saniye sonra temizle.\n6. Sahneyi kaydet ve Play Mode'da dogrula.\n\nBu plan sahneye uygulanabilir; devam etmek icin Onayla ve uygula dugmesine basin.",
                "APPLICABLE PLAN\n\n1. Add a Ball Pop Lightning Observer to the active scene.\n2. Observe existing coloured ball-hit effects as the event source.\n3. Spawn the Lightning Hit Blue prefab 5.5 units above the pop position.\n4. Move the strike down to the pop point in 0.18 seconds.\n5. Clean up the effect after 2 seconds.\n6. Save the scene and verify it in Play Mode.\n\nThis plan can be applied to the scene; press Approve and apply to continue.");
            return true;
        }

        public static bool Apply(string featureId, out string message)
        {
            if (featureId != BallPopLightning)
            {
                message = AIEngineerLocalization.Text("Bu ozellik henuz otomatik uygulanamiyor.", "This feature cannot be applied automatically yet.");
                return false;
            }
            return InstallBallPopLightning(out message);
        }

        public static bool InstallBallPopLightning(out string message)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(LightningPrefabPath);
            if (prefab == null)
            {
                message = AIEngineerLocalization.Text(
                    "Lightning Hit Blue prefabi bulunamadi: " + LightningPrefabPath,
                    "Lightning Hit Blue prefab was not found: " + LightningPrefabPath);
                return false;
            }

            var observer = Object.FindFirstObjectByType<BallPopLightningObserver>();
            if (observer == null)
            {
                var host = new GameObject("AI Feature - Ball Pop Lightning");
                Undo.RegisterCreatedObjectUndo(host, "Install Ball Pop Lightning");
                observer = host.AddComponent<BallPopLightningObserver>();
            }
            Undo.RecordObject(observer, "Configure Ball Pop Lightning");
            observer.Configure(prefab);
            EditorUtility.SetDirty(observer);
            EditorSceneManager.MarkSceneDirty(observer.gameObject.scene);
            EditorSceneManager.SaveScene(observer.gameObject.scene);
            message = AIEngineerLocalization.Text(
                "Top patlamasi yildirim ozelligi aktif sahneye uygulandi ve sahne kaydedildi.",
                "Ball-pop lightning was applied to the active scene and the scene was saved.");
            return true;
        }

        [InitializeOnLoadMethod]
        private static void ApplyPendingFeatureAfterReload()
        {
            EditorApplication.delayCall += () =>
            {
                if (!System.IO.File.Exists(PendingInstallPath)) return;
                AssetDatabase.DeleteAsset(PendingInstallPath);
                AssetDatabase.SaveAssets();
                if (InstallBallPopLightning(out var result)) Debug.Log("[AI] " + result);
                else Debug.LogError("[AI] " + result);
            };
        }

        private static string Normalize(string value)
        {
            var decomposed = (value ?? string.Empty).ToLowerInvariant().Normalize(NormalizationForm.FormD);
            var output = new StringBuilder();
            foreach (var character in decomposed)
            {
                if (CharUnicodeInfo.GetUnicodeCategory(character) == UnicodeCategory.NonSpacingMark) continue;
                output.Append(character == 'ı' ? 'i' : character);
            }
            return output.ToString().Normalize(NormalizationForm.FormC);
        }
    }
}
