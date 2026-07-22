using UnityEditor;
using UnityEngine;

namespace AIEngineer.Editor
{
    /// <summary>Small, always-accessible account setup window independent of Control Center layout.</summary>
    public sealed class AIEngineerProviderWindow : EditorWindow
    {
        [MenuItem("AI Engineer/Providers/Hesap Baglantilari")]
        public static void Open()
        {
            var window = GetWindow<AIEngineerProviderWindow>(true, "AI Hesap Baglantilari");
            window.minSize = new Vector2(460f, 370f);
            window.Show();
        }

        [MenuItem("AI Engineer/Providers/Codex Plus Girisini Ac")]
        private static void OpenCodexLoginFromMenu() => ProviderSetupManager.OpenCodexLogin();

        [MenuItem("AI Engineer/Providers/Qwen Baglantisini Ac")]
        private static void OpenQwenLoginFromMenu() => ProviderSetupManager.OpenQwenAccountSignIn();

        private void OnGUI()
        {
            GUILayout.Space(14f);
            GUILayout.Label("AI HESAP BAGLANTILARI", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox(
                "Bu pencere kullanici adi veya sifre istemez. Girisler Qwen ve OpenAI'nin kendi guvenli tarayici akislariyla yapilir.",
                MessageType.Info);

            GUILayout.Space(10f);
            GUILayout.Label("CODEX PLUS", EditorStyles.boldLabel);
            GUILayout.Label("ChatGPT Plus hesabinla Codex CLI oturumu acilir.", EditorStyles.wordWrappedMiniLabel);
            if (GUILayout.Button("Codex Plus girisini ac", GUILayout.Height(34f)))
                ProviderSetupManager.OpenCodexLogin();

            GUILayout.Space(16f);
            GUILayout.Label("QWEN CODE", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox(
                ProviderSetupManager.QwenProviderStatus,
                ProviderSetupManager.IsQwenProviderConfigured ? MessageType.Info : MessageType.Warning);
            GUILayout.Label("Tarayicida saglayici girisini tamamla; acilan Qwen terminalinde /auth yaz.", EditorStyles.wordWrappedMiniLabel);
            if (GUILayout.Button("Qwen hesabini bagla (tarayici)", GUILayout.Height(34f)))
                ProviderSetupManager.OpenQwenAccountSignIn();
            if (GUILayout.Button("Qwen baglantisini kontrol et", GUILayout.Height(26f)))
                Repaint();
        }
    }
}
