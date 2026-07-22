using System;
using System.Diagnostics;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;

namespace AIEngineer.Editor
{
    /// <summary>Stores portable CLI paths and opens interactive provider login terminals.</summary>
    public static class ProviderSetupManager
    {
        private const string QwenKey = "AIEngineer.QwenExecutable";
        private const string CodexKey = "AIEngineer.CodexExecutable";
        private const string QwenModelStudioUrl = "https://bailian.console.alibabacloud.com/";

        public static string QwenExecutable
        {
            get => EditorPrefs.GetString(QwenKey, DefaultQwenPath());
            set => EditorPrefs.SetString(QwenKey, string.IsNullOrWhiteSpace(value) ? "qwen" : value);
        }

        public static string CodexExecutable
        {
            get => EditorPrefs.GetString(CodexKey, DefaultCodexPath());
            set => EditorPrefs.SetString(CodexKey, string.IsNullOrWhiteSpace(value) ? "codex" : value);
        }

        public static void OpenQwenSetup()
        {
            var qwenHome = QwenHome;
            Directory.CreateDirectory(qwenHome);
            OpenTerminal(QwenExecutable, string.Empty, "QWEN_HOME", qwenHome);
        }

        /// <summary>Starts the provider-owned browser login and the matching Qwen Code terminal. Passwords never enter Unity.</summary>
        public static void OpenQwenAccountSignIn()
        {
            UnityEngine.Application.OpenURL(QwenModelStudioUrl);
            OpenQwenSetup();
            EditorUtility.DisplayDialog(
                "AI Engineer - Qwen",
                "Qwen hesabini tarayicida baglayin. Ardindan acilan Qwen Code terminalinde /auth yazin ve Alibaba ModelStudio > Coding Plan veya sahip oldugunuz API anahtari secenegini tamamlayin.\n\nQwen.ai Gmail oturumu Unity tarafinda sifre olarak saklanmaz.",
                "Tamam");
        }

        public static bool IsQwenProviderConfigured => TryGetQwenProvider(out _);

        public static string QwenProviderStatus
        {
            get
            {
                if (!TryGetQwenProvider(out var provider))
                    return "Qwen hesabi bagli degil. Tarayici girisini baslatin, sonra terminalde /auth kullanin.";
                return "Qwen bagli: " + provider;
            }
        }

        public static void OpenCodexLogin() => OpenTerminal(CodexExecutable, "login");

        private static void OpenTerminal(string executable, string arguments, string environmentName = "", string environmentValue = "")
        {
            try
            {
                var environmentPrefix = string.IsNullOrWhiteSpace(environmentName)
                    ? string.Empty
                    : "set \"" + environmentName + "=" + environmentValue.Replace("\"", string.Empty) + "\" && ";
                var command = environmentPrefix + Quote(executable) + (string.IsNullOrWhiteSpace(arguments) ? string.Empty : " " + arguments);
                Process.Start(new ProcessStartInfo
                {
                    FileName = Environment.GetEnvironmentVariable("COMSPEC") ?? "cmd.exe",
                    Arguments = "/k " + command,
                    UseShellExecute = true,
                });
            }
            catch (Exception error)
            {
                UnityEngine.Debug.LogError("[AI] Provider terminal could not be opened: " + error.Message);
            }
        }

        private static string DefaultCodexPath()
        {
            var local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var standalone = Path.Combine(local, "Programs", "OpenAI", "Codex", "bin", "codex.exe");
            return File.Exists(standalone) ? standalone : "codex";
        }

        private static string DefaultQwenPath()
        {
            var bundled = Path.Combine(ServerManager.BackendRoot, "Tools", "QwenCode", "bin", "qwen.cmd");
            return File.Exists(bundled) ? bundled : "qwen";
        }

        private static string Quote(string value) => "\"" + (value ?? string.Empty).Replace("\"", "\"\"") + "\"";

        private static string QwenHome => Path.Combine(ServerManager.BackendRoot, ".runtime", "qwen");

        private static bool TryGetQwenProvider(out string provider)
        {
            provider = string.Empty;
            var settings = Path.Combine(QwenHome, "settings.json");
            if (!File.Exists(settings)) return false;
            try
            {
                var content = File.ReadAllText(settings);
                var selectedType = Regex.Match(content, "\\\"selectedType\\\"\\s*:\\s*\\\"([^\\\"]+)\\\"");
                if (selectedType.Success)
                {
                    provider = selectedType.Groups[1].Value;
                    return !string.IsNullOrWhiteSpace(provider);
                }
                if (content.IndexOf("\"modelProviders\"", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    provider = "custom provider";
                    return true;
                }
            }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
            return false;
        }
    }
}
