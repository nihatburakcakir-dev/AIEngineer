using AIEngineer.Games;
using UnityEditor;
using UnityEngine;

namespace AIEngineer.Editor.Features
{
    /// <summary>Runs a small Play Mode smoke test for supported scene features.</summary>
    [InitializeOnLoad]
    public static class FeatureAcceptanceRunner
    {
        private const string PendingTestPath = "Assets/AIEngineer/RunBallPopLightningAcceptance.request";
        private const string SessionKey = "AIEngineer.BallPopLightningAcceptance";
        private static GameObject probe;
        private static double deadline;

        static FeatureAcceptanceRunner()
        {
            EditorApplication.playModeStateChanged -= OnPlayModeStateChanged;
            EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
            EditorApplication.delayCall += ConsumePendingTest;
        }

        [MenuItem("AI Engineer/Games/Validate Ball-Pop Lightning")]
        public static void RunBallPopLightningTest()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning("[AI Acceptance] Play Mode is already active; validation was not started.");
                return;
            }
            if (Object.FindFirstObjectByType<BallPopLightningObserver>() == null &&
                !FeatureApplicationService.InstallBallPopLightning(out var installMessage))
            {
                Debug.LogError("[AI Acceptance] " + installMessage);
                return;
            }

            SessionState.SetBool(SessionKey, true);
            Debug.Log("[AI Acceptance] Ball-pop lightning Play Mode validation started.");
            EditorApplication.isPlaying = true;
        }

        private static void ConsumePendingTest()
        {
            if (!System.IO.File.Exists(PendingTestPath)) return;
            AssetDatabase.DeleteAsset(PendingTestPath);
            AssetDatabase.SaveAssets();
            RunBallPopLightningTest();
        }

        private static void OnPlayModeStateChanged(PlayModeStateChange state)
        {
            if (!SessionState.GetBool(SessionKey, false)) return;
            if (state == PlayModeStateChange.EnteredPlayMode)
            {
                probe = new GameObject("Blue Hit Acceptance Probe");
                probe.AddComponent<ParticleSystem>().Play();
                deadline = EditorApplication.timeSinceStartup + 3.0;
                EditorApplication.update -= AwaitLightning;
                EditorApplication.update += AwaitLightning;
            }
            else if (state == PlayModeStateChange.EnteredEditMode)
            {
                EditorApplication.update -= AwaitLightning;
                SessionState.SetBool(SessionKey, false);
            }
        }

        private static void AwaitLightning()
        {
            if (GameObject.Find("AI Ball Pop Lightning") != null)
            {
                Complete(true, "Observer created a falling lightning effect for a new ball-hit particle root.");
                return;
            }
            if (EditorApplication.timeSinceStartup >= deadline)
                Complete(false, "No lightning effect was detected within three seconds.");
        }

        private static void Complete(bool success, string detail)
        {
            EditorApplication.update -= AwaitLightning;
            if (probe != null) Object.Destroy(probe);
            probe = null;
            SessionState.SetBool(SessionKey, false);
            if (success) Debug.Log("[AI Acceptance] PASS: " + detail);
            else Debug.LogError("[AI Acceptance] FAIL: " + detail);
            EditorApplication.isPlaying = false;
        }
    }
}
