using UnityEngine;
using UnityEditor;
using System.Diagnostics;
using System.IO;
using System;
using System.Net;

namespace AIEngineer.Editor
{
    public static class ServerManager
    {
        private const string BackendRootKey = "AIEngineer.BackendRoot";
        private const string PythonExecutableKey = "AIEngineer.PythonExecutable";
        static Process process;
        static bool endpointRunning;
        static double nextEndpointProbe;

        public static string BackendRoot
        {
            get
            {
                var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
                var configured = EditorPrefs.GetString(BackendRootKey, string.Empty);
                if (HasBackend(configured)) return configured;

                var besideProject = Path.Combine(projectRoot, "AIEngineerBackend");
                if (HasBackend(besideProject)) return besideProject;

                var developmentWorkspace = @"C:\AIEngineer";
                if (HasBackend(developmentWorkspace)) return developmentWorkspace;

                return string.IsNullOrWhiteSpace(configured) ? besideProject : configured;
            }
            set => EditorPrefs.SetString(BackendRootKey, value ?? string.Empty);
        }

        public static string PythonExecutable
        {
            get
            {
                var configured = EditorPrefs.GetString(PythonExecutableKey, string.Empty);
                if (File.Exists(configured)) return configured;

                var backendPython = Path.Combine(BackendRoot, ".venv", "Scripts", "python.exe");
                if (File.Exists(backendPython)) return backendPython;

                var userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                var bundledPython = Path.Combine(userProfile, ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "python.exe");
                if (File.Exists(bundledPython)) return bundledPython;

                return "py";
            }
            set => EditorPrefs.SetString(PythonExecutableKey, value ?? string.Empty);
        }

        public static bool HasBackend(string root) => !string.IsNullOrWhiteSpace(root) &&
            (File.Exists(Path.Combine(root, "Source", "Server", "autonomous_server.py")) ||
             File.Exists(Path.Combine(root, "Source", "Server", "server.py")));

        public static bool IsRunning
        {
            get
            {
                try
                {
                    if (process != null && !process.HasExited) return true;
                }
                catch { process = null; }
                if (EditorApplication.timeSinceStartup < nextEndpointProbe) return endpointRunning;
                nextEndpointProbe = EditorApplication.timeSinceStartup + 2d;
                endpointRunning = ProbeEndpoint();
                return endpointRunning;
            }
        }

        public static void Start()
        {
            if (IsRunning)
                return;

            string root = BackendRoot;
            if (!HasBackend(root))
            {
                UnityEngine.Debug.LogError("[AI] " + AIEngineerLocalization.Text(
                    "Python backend bulunamadi. AIEngineer-Python-Backend.zip dosyasini cikartip klasoru AI Engineer > Control Center icinden secin.",
                    "Python backend not found. Extract AIEngineer-Python-Backend.zip, then choose its folder in AI Engineer > Control Center."));
                return;
            }

            process = new Process();

            var python = PythonExecutable;
            process.StartInfo.FileName = python;

            process.StartInfo.Arguments =
                string.Equals(python, "py", StringComparison.OrdinalIgnoreCase)
                    ? "-3 -m Source.Server.autonomous_server"
                    : "-m Source.Server.autonomous_server";

            process.StartInfo.WorkingDirectory =
                root;

            process.StartInfo.UseShellExecute = false;

            process.StartInfo.CreateNoWindow = true;

            process.StartInfo.RedirectStandardOutput = true;

            process.StartInfo.RedirectStandardError = true;

            process.StartInfo.EnvironmentVariables["AIENGINEER_QWEN_EXECUTABLE"] = ProviderSetupManager.QwenExecutable;
            process.StartInfo.EnvironmentVariables["AIENGINEER_CODEX_EXECUTABLE"] = ProviderSetupManager.CodexExecutable;

            process.OutputDataReceived +=
                (s, e) =>
                {
                    if (!string.IsNullOrWhiteSpace(e.Data))
                        UnityEngine.Debug.Log("[AI] " + e.Data);
                };

            process.ErrorDataReceived +=
                (s, e) =>
                {
                    if (!string.IsNullOrWhiteSpace(e.Data))
                    {
                        if (e.Data.Contains(" 200 -") || e.Data.Contains("\" 200 "))
                            UnityEngine.Debug.Log("[AI] " + e.Data);
                        else
                            UnityEngine.Debug.LogError("[AI] " + e.Data);
                    }
                };

            try
            {
                process.Start();

                process.BeginOutputReadLine();

                process.BeginErrorReadLine();

                UnityEngine.Debug.Log(
                    "[AI] Server Started"
                );
                endpointRunning = true;
            }
            catch (System.Exception ex)
            {
                UnityEngine.Debug.LogError(
                    "[AI] " + AIEngineerLocalization.Text(
                        "Python baslatilamadi. Control Center icinden Python calistirilabilir dosyasini secin. ",
                        "Python could not start. Choose the Python executable in Control Center. ") + ex.Message
                );
                process?.Dispose();
                process = null;
            }
        }

        public static void Stop()
        {
            try
            {
                if (process != null && !process.HasExited)
                    process.Kill();
                process?.Dispose();
            }
            catch (System.Exception error)
            {
                UnityEngine.Debug.LogWarning("[AI] Backend process could not be stopped: " + error.Message);
            }
            finally { process = null; }
            endpointRunning = false;

            UnityEngine.Debug.Log(
                "[AI] Server Stopped"
            );
        }

        public static void Restart()
        {
            Stop();

            Start();
        }

        private static bool ProbeEndpoint()
        {
            try
            {
                var request = WebRequest.CreateHttp("http://127.0.0.1:8080/health");
                request.Method = "GET";
                request.Timeout = 250;
                using var response = (HttpWebResponse)request.GetResponse();
                return response.StatusCode == HttpStatusCode.OK;
            }
            catch { return false; }
        }
    }
}
