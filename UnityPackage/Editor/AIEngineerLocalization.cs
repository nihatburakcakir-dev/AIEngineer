using UnityEditor;

namespace AIEngineer.Editor
{
    public enum AIEngineerLanguage
    {
        Turkish = 0,
        English = 1,
    }

    /// <summary>Small editor-only localization service with a persisted user preference.</summary>
    public static class AIEngineerLocalization
    {
        private const string LanguageKey = "AIEngineer.Language";

        public static AIEngineerLanguage Current
        {
            get => (AIEngineerLanguage)EditorPrefs.GetInt(LanguageKey, (int)AIEngineerLanguage.Turkish);
            set => EditorPrefs.SetInt(LanguageKey, (int)value);
        }

        public static string Text(string turkish, string english) => Current == AIEngineerLanguage.Turkish ? turkish : english;

        public static string[] Sections => Current == AIEngineerLanguage.Turkish
            ? new[] { "Olustur", "Analiz", "Onar" }
            : new[] { "Build", "Analyze", "Repair" };

        public static string[] QuickPrompts => QuickPromptsFor(0);

        public static string[] QuickPromptsFor(int section)
        {
            if (Current == AIEngineerLanguage.Turkish)
            {
                return section switch
                {
                    0 => new[] { "Yeni bir oyun sistemi olustur", "Oyunun temasini ve amacini anlatan mobil giris UI prefab'i olustur", "Object pool sistemi olustur", "Yeni prefab ve controller olustur" },
                    1 => new[] { "Aktif sahneyi teknik olarak analiz et", "Secili scripti performans acisindan incele", "Eksik referanslari kontrol et", "Mobil uyumlulugu analiz et" },
                    _ => new[] { "Console hatasini analiz edip onarim plani olustur", "Bozuk mekanigi duzelt", "Eksik script referanslarini onar", "Mobil giris sorununu duzelt" },
                };
            }

            return section switch
            {
                0 => new[] { "Create a new game system", "Create a mobile entrance UI prefab that explains the game's theme and objective", "Create an object pool system", "Create a new prefab and controller" },
                1 => new[] { "Analyze the active scene technically", "Review the selected script for performance issues", "Check for missing references", "Analyze mobile compatibility" },
                _ => new[] { "Analyze the Console error and create a repair plan", "Repair a broken mechanic", "Repair missing script references", "Fix a mobile input issue" },
            };
        }

        public static string DefaultPrompt => Text(
            "Aktif Unity sahnesini analiz et ve guvenli bir uygulama plani cikar.",
            "Analyze the active Unity scene and create a safe implementation plan.");
    }
}
