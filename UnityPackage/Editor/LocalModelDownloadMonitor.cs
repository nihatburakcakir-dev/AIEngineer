using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace AIEngineer.Editor
{
    internal enum LocalModelDownloadState { Unknown, Downloading, Ready, Missing }

    internal readonly struct LocalModelDownloadStatus
    {
        public readonly LocalModelDownloadState State;
        public readonly string Message;

        public LocalModelDownloadStatus(LocalModelDownloadState state, string message)
        {
            State = state;
            Message = message;
        }
    }

    /// <summary>Shows actual sparse-file allocation progress for Ollama's qwen3:30b download.</summary>
    internal static class LocalModelDownloadMonitor
    {
        private const string ModelName = "qwen3:30b";
        private const long ModelBytes = 18_556_685_856L;
        private static LocalModelDownloadStatus cached = new(LocalModelDownloadState.Unknown, "Yerel model durumu okunuyor...");
        private static DateTime lastRefreshUtc = DateTime.MinValue;

        public static LocalModelDownloadStatus Current
        {
            get
            {
                if ((DateTime.UtcNow - lastRefreshUtc).TotalSeconds >= 3) Refresh();
                return cached;
            }
        }

        public static void Refresh()
        {
            lastRefreshUtc = DateTime.UtcNow;
            try
            {
                if (Run("ollama", "list", out var models) && models.IndexOf(ModelName, StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    cached = new LocalModelDownloadStatus(LocalModelDownloadState.Ready, "qwen3:30b hazir (yaklasik 19 GB). Yerel otonom model etkin.");
                    return;
                }

                var blobs = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".ollama", "models", "blobs");
                var partial = Directory.Exists(blobs)
                    ? new DirectoryInfo(blobs).GetFiles("*-partial").OrderByDescending(file => file.Length).FirstOrDefault()
                    : null;
                if (partial == null)
                {
                    cached = new LocalModelDownloadStatus(LocalModelDownloadState.Missing, "qwen3:30b henuz indirilmeye baslamadi.");
                    return;
                }

                var downloaded = AllocatedBytes(partial.FullName);
                var percent = Math.Clamp(downloaded * 100d / ModelBytes, 0d, 99.9d);
                cached = new LocalModelDownloadStatus(
                    LocalModelDownloadState.Downloading,
                    $"qwen3:30b indiriliyor: %{percent:0.0} ({ToGiB(downloaded):0.00} / {ToGiB(ModelBytes):0.00} GiB)");
            }
            catch (Exception error)
            {
                cached = new LocalModelDownloadStatus(LocalModelDownloadState.Unknown, "Yerel model durumu okunamadi: " + error.Message);
            }
        }

        private static long AllocatedBytes(string path)
        {
            if (!Run("fsutil.exe", "sparse queryrange \"" + path + "\"", out var output)) return 0;
            long total = 0;
            foreach (Match match in Regex.Matches(output, @"Length:\s*0x([0-9a-fA-F]+)"))
                total += long.Parse(match.Groups[1].Value, NumberStyles.HexNumber, CultureInfo.InvariantCulture);
            return total;
        }

        private static bool Run(string executable, string arguments, out string output)
        {
            output = string.Empty;
            try
            {
                using var process = Process.Start(new ProcessStartInfo
                {
                    FileName = executable,
                    Arguments = arguments,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                });
                if (process == null) return false;
                output = process.StandardOutput.ReadToEnd();
                process.WaitForExit(1500);
                return process.ExitCode == 0;
            }
            catch { return false; }
        }

        private static double ToGiB(long value) => value / 1024d / 1024d / 1024d;
    }
}
