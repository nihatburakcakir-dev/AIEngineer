using UnityEngine;
using UnityEditor;
using System.Diagnostics;
using System.IO;

namespace AIEngineer.Editor
{
    public static class ServerManager
    {
        static Process process;

        public static bool IsRunning
        {
            get
            {
                return process != null &&
                       !process.HasExited;
            }
        }

        public static void Start()
        {
            if (IsRunning)
                return;

            string root =
                @"C:\AIEngineer";

            process = new Process();

            process.StartInfo.FileName = "py";

            process.StartInfo.Arguments =
                "-3 -m Source.Server.server";

            process.StartInfo.WorkingDirectory =
                root;

            process.StartInfo.UseShellExecute = false;

            process.StartInfo.CreateNoWindow = true;

            process.StartInfo.RedirectStandardOutput = true;

            process.StartInfo.RedirectStandardError = true;

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
                        UnityEngine.Debug.LogError("[AI] " + e.Data);
                };

            try
            {
                process.Start();

                process.BeginOutputReadLine();

                process.BeginErrorReadLine();

                UnityEngine.Debug.Log(
                    "[AI] Server Started"
                );
            }
            catch (System.Exception ex)
            {
                UnityEngine.Debug.LogError(
                    "[AI] " + ex.Message
                );
            }
        }

        public static void Stop()
        {
            if (!IsRunning)
                return;

            process.Kill();

            process.Dispose();

            process = null;

            UnityEngine.Debug.Log(
                "[AI] Server Stopped"
            );
        }

        public static void Restart()
        {
            Stop();

            Start();
        }
    }
}
