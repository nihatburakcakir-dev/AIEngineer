using System;
using System.Text;
using UnityEngine;

namespace AIEngineer.Editor.Autonomy
{
    [Serializable]
    public sealed class AutonomousChangeSet
    {
        public string protocol;
        public string requestId;
        public string summary;
        public string risk;
        public bool requiresConfirmation;
        public AutonomousChangeOperation[] operations;
        public AutonomousValidation validation;
        public string[] explanation;
        public string[] warnings;
        public string model;
        public string responseType;
        public string answer;

        public bool IsAnswer => string.Equals(responseType, "answer", StringComparison.OrdinalIgnoreCase);
        public bool HasOperations => operations != null && operations.Length > 0;
        public bool IsValid => protocol == "ai-engineer.change-set/v1" && (IsAnswer ? !string.IsNullOrWhiteSpace(answer) : HasOperations);
    }

    [Serializable]
    public sealed class AutonomousValidation
    {
        public bool compile = true;
        public bool playMode;
        public string[] checks;
    }

    [Serializable]
    public sealed class AutonomousChangeOperation
    {
        public string id;
        public string kind;
        public string path;
        public string assetPath;
        public string scenePath;
        public string targetPath;
        public string name;
        public string parentPath;
        public string primitive;
        public string component;
        public string property;
        public string content;
        public string search;
        public string replacement;
        public string shader;
        public string color;
        public string sourceImagePath;
        public string dimension;
        public string gameKey;
        public string title;
        public string subtitle;
        public string buttonLabel;
        public string theme;
        public string[] highlights;
        public string referenceMode;
        public string referenceLayout;
        public string imageFit;
        public string ctaAnchor;
        public bool replaceExisting;
        public string orientation;
        public string gameplayTarget;
        public string gameplayScenePath;
        public bool pulseAccent;
        public string objectPath;
        public string value;
        public string valueType;
        public bool overwrite;
        public float[] position;
        public float[] rotation;
        public float[] scale;
        public float duration = 2f;
        public float startSpeed = 3f;
        public float startSize = 0.35f;
        public int maxParticles = 120;
        public string shape;
        public string[] systems;
        public AutonomousComponentSpec[] components;
        public AutonomousPropertySpec[] properties;
    }

    [Serializable]
    public sealed class AutonomousComponentSpec
    {
        public string type;
        public AutonomousPropertySpec[] properties;
    }

    [Serializable]
    public sealed class AutonomousPropertySpec
    {
        public string name;
        public string type;
        public string value;
        public string objectPath;
    }

    [Serializable]
    internal sealed class AutonomousPlanRequest
    {
        public string prompt;
        public string projectPath;
        public string activeScene;
        public string imagePath;
        public string modelMode;
        public string visionMode;
        public string targetOrientation;
        public string language;
        public string[] selectedAssets;
        public AIEngineer.Scene.SceneObjectModel[] objects;
        public AIEngineer.Scene.ProjectModel project;
    }

    [Serializable]
    internal sealed class AutonomousRepairRequest
    {
        public string prompt;
        public string projectPath;
        public string activeScene;
        public string imagePath;
        public string modelMode;
        public string visionMode;
        public string targetOrientation;
        public string language;
        public string[] selectedAssets;
        public AIEngineer.Scene.SceneObjectModel[] objects;
        public AIEngineer.Scene.ProjectModel project;
        public AutonomousChangeSet changeSet;
        public string[] diagnostics;
        public int attempt;
    }

    public static class AutonomousChangeSetFormatter
    {
        public static string Format(AutonomousChangeSet changeSet)
        {
            if (changeSet == null) return "No change set.";
            if (changeSet.IsAnswer) return changeSet.answer ?? string.Empty;
            var output = new StringBuilder();
            output.AppendLine(AIEngineerLocalization.Text("UYGULANABILIR DEGISIKLIK SETI", "EXECUTABLE CHANGE SET"));
            output.AppendLine(changeSet.summary ?? string.Empty);
            output.AppendLine();
            output.Append(AIEngineerLocalization.Text("Risk: ", "Risk: ")).AppendLine(changeSet.risk ?? "MEDIUM");
            output.Append(AIEngineerLocalization.Text("Model: ", "Model: ")).AppendLine(changeSet.model ?? "local");
            output.AppendLine();
            if (changeSet.operations != null)
            {
                for (var index = 0; index < changeSet.operations.Length; index++)
                {
                    var operation = changeSet.operations[index];
                    output.Append(index + 1).Append(". ").Append(operation.kind);
                    var target = First(operation.path, operation.assetPath, operation.scenePath, operation.targetPath, operation.name);
                    if (!string.IsNullOrWhiteSpace(target)) output.Append(" -> ").Append(target);
                    output.AppendLine();
                }
            }
            if (changeSet.explanation != null && changeSet.explanation.Length > 0)
            {
                output.AppendLine();
                output.AppendLine(AIEngineerLocalization.Text("NEDEN", "RATIONALE"));
                foreach (var line in changeSet.explanation) output.Append("- ").AppendLine(LocalizeGeneratedText(line));
            }
            if (changeSet.warnings != null && changeSet.warnings.Length > 0)
            {
                output.AppendLine();
                output.AppendLine(AIEngineerLocalization.Text("UYARILAR", "WARNINGS"));
                foreach (var warning in changeSet.warnings) output.Append("- ").AppendLine(LocalizeGeneratedText(warning));
            }
            output.AppendLine();
            output.Append(AIEngineerLocalization.Text(
                "Bu set henuz uygulanmadi. Otonom uygula, once yedek alir; derleme basarisizsa duzeltme ister veya geri alir.",
                "This set is not applied yet. Autonomous apply backs up first; if compilation fails it requests a repair or rolls back."));
            return output.ToString();
        }

        private static string First(params string[] values)
        {
            foreach (var value in values)
                if (!string.IsNullOrWhiteSpace(value)) return value;
            return string.Empty;
        }

        private static string LocalizeGeneratedText(string text)
        {
            if (AIEngineerLocalization.Current == AIEngineerLanguage.English) return text ?? string.Empty;
            return (text ?? string.Empty)
                .Replace("Model JSON tail was truncated after a complete operation manifest; trailing prose was omitted.", "Model JSON çıktısının sonu kesildi; tamamlanmış işlem listesi güvenle korundu.")
                .Replace("Model JSON tail was truncated; the complete answer text was recovered safely.", "Model JSON çıktısının sonu kesildi; tamamlanmış yanıt metni güvenle kurtarıldı.")
                .Replace("A redundant component operation targeting an asset file was omitted because create_ui_screen creates its own controls.", "Varlık dosyasını hedefleyen gereksiz component işlemi çıkarıldı; create_ui_screen kendi kontrollerini oluşturur.")
                .Replace("UI operation was simplified because create_ui_screen creates its own controls and related UI assets.", "UI işlemi sadeleştirildi; create_ui_screen kendi kontrollerini ve ilgili UI varlıklarını oluşturur.");
        }
    }
}
