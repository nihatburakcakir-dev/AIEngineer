using System;
using System.IO;
using System.Linq;
using System.Text;
using Process = System.Diagnostics.Process;
using ProcessStartInfo = System.Diagnostics.ProcessStartInfo;
using AIEngineer.Editor.Autonomy;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace AIEngineer.Editor
{
    /// <summary>Original Unity production dashboard for the local-first toolchain.</summary>
    public sealed class AIEngineerControlCenter : EditorWindow
    {
        // Unity 6 forbids Texture2D construction in a ScriptableObject type
        // initializer. These editor-only textures are created lazily after the
        // window instance is enabled instead.
        private static Texture2D HeaderTexture;
        private static Texture2D SidebarTexture;
        private static Texture2D InspectorTexture;
        private static Texture2D PrimaryButtonTexture;
        private static Texture2D SecondaryButtonTexture;
        private static Texture2D ActiveButtonTexture;
        private int activeSection;
        private int selectedQuickPrompt;
        private string prompt;
        private string status;
        private string lastResponse;
        private bool isRunning;
        [SerializeField] private AutonomousChangeSet pendingChangeSet;
        private string referenceImagePath;
        private int modelModeIndex;
        private bool fullAutonomy = true;
        private int maxRepairAttempts = 3;
        private string imagePrompt;
        private string imageOutputName;
        private int imageSizeIndex = 1;
        private float imageEditStrength = 0.78f;
        private Vector2 workspaceScroll;
        private Vector2 responseScroll;

        [MenuItem("AI Engineer/Control Center")]
        public static void Open()
        {
            var window = GetWindow<AIEngineerControlCenter>("AI Engineer");
            window.minSize = new Vector2(860f, 560f);
            window.Show();
        }

        private void OnEnable()
        {
            EnsureTextures();
            activeSection = Mathf.Clamp(activeSection, 0, AIEngineerLocalization.Sections.Length - 1);
            if (string.IsNullOrWhiteSpace(prompt)) prompt = AIEngineerLocalization.DefaultPrompt;
            if (string.IsNullOrWhiteSpace(status)) status = L("Hazir. Bir istek yazin veya hazir gorev secin.", "Ready. Enter a request or choose a quick task.");
            if (string.IsNullOrWhiteSpace(lastResponse)) lastResponse = L("Henuz bir yanit yok.", "No response yet.");
            if (string.IsNullOrWhiteSpace(imagePrompt)) imagePrompt = L("2D oyun Sprite'i, temiz siluet, metinsiz", "2D game Sprite, clean silhouette, no text");
            if (string.IsNullOrWhiteSpace(imageOutputName)) imageOutputName = "GeneratedSprite";
        }

        private void OnGUI()
        {
            EnsureTextures();
            DrawHeader();
            EditorGUILayout.BeginHorizontal();
            DrawSidebar();
            DrawWorkspace();
            DrawInspector();
            EditorGUILayout.EndHorizontal();
        }

        private void OnInspectorUpdate()
        {
            Repaint();
        }

        private void DrawHeader()
        {
            var header = new GUIStyle(EditorStyles.helpBox) { padding = new RectOffset(18, 18, 13, 13) };
            header.normal.background = HeaderTexture;
            EditorGUILayout.BeginHorizontal(header, GUILayout.Height(74f));
            EditorGUILayout.BeginVertical();
            GUILayout.Label("AI ENGINEER", TitleStyle());
            GUILayout.Label(L("Unity uretim masasi / yerel-oncelikli / degisiklikten once incele", "Unity production desk / local-first / review before change"), MutedStyle());
            EditorGUILayout.EndVertical();
            GUILayout.FlexibleSpace();
            var previousLanguage = (int)AIEngineerLocalization.Current;
            var nextLanguage = EditorGUILayout.Popup(previousLanguage, new[] { "Türkçe", "English" }, GUILayout.Width(92f));
            if (nextLanguage != previousLanguage)
            {
                AIEngineerLocalization.Current = (AIEngineerLanguage)nextLanguage;
                status = L("Dil Turkce olarak ayarlandi.", "Language set to English.");
                Repaint();
            }
            GUILayout.Space(12f);
            GUILayout.Label(ServerManager.IsRunning ? L("YEREL MOTOR CEVRIMICI", "LOCAL ENGINE ONLINE") : L("YEREL MOTOR ISTEGE BAGLI", "LOCAL ENGINE OPTIONAL"), StatusStyle(ServerManager.IsRunning));
            EditorGUILayout.EndHorizontal();
        }

        private void DrawSidebar()
        {
            var sidebar = new GUIStyle(EditorStyles.helpBox) { padding = new RectOffset(10, 10, 12, 12) };
            sidebar.normal.background = SidebarTexture;
            EditorGUILayout.BeginVertical(sidebar, GUILayout.Width(124f), GUILayout.ExpandHeight(true));
            var sections = AIEngineerLocalization.Sections;
            GUILayout.Label(L("CALISMA ALANI", "WORKSPACE"), SmallLabelStyle());
            GUILayout.Space(8f);
            for (var index = 0; index < sections.Length; index++)
            {
                var selected = activeSection == index;
                var button = new GUIStyle(GUI.skin.button) { alignment = TextAnchor.MiddleLeft, fixedHeight = 30f, padding = new RectOffset(12, 8, 4, 4) };
                button.normal.background = selected ? ActiveButtonTexture : SecondaryButtonTexture;
                button.hover.background = ActiveButtonTexture;
                button.normal.textColor = selected ? new Color(0.72f, 0.92f, 1f) : new Color(0.78f, 0.8f, 0.84f);
                if (GUILayout.Button((selected ? "◆  " : "   ") + sections[index], button))
                {
                    activeSection = index;
                    selectedQuickPrompt = 0;
                    prompt = AIEngineerLocalization.QuickPromptsFor(index)[0];
                }
            }
            GUILayout.FlexibleSpace();
            GUILayout.Label("Unity " + Application.unityVersion, MutedStyle());
            GUILayout.Label(L("Sahne: ", "Scene: ") + EditorSceneManager.GetActiveScene().name, MutedStyle());
            EditorGUILayout.EndVertical();
        }

        private void DrawWorkspace()
        {
            EditorGUILayout.BeginVertical(GUILayout.ExpandWidth(true), GUILayout.ExpandHeight(true));
            workspaceScroll = EditorGUILayout.BeginScrollView(workspaceScroll, true, true, GUILayout.ExpandWidth(true), GUILayout.ExpandHeight(true));
            GUILayout.Space(12f);
            var sections = AIEngineerLocalization.Sections;
            var quickPrompts = AIEngineerLocalization.QuickPromptsFor(activeSection);
            selectedQuickPrompt = Mathf.Clamp(selectedQuickPrompt, 0, quickPrompts.Length - 1);
            GUILayout.Label(sections[activeSection].ToUpperInvariant() + " " + L("ISTEGI", "REQUEST"), SectionStyle());
            GUILayout.Label(SectionHint(), MutedStyle());
            GUILayout.Space(10f);
            var previousQuickPrompt = selectedQuickPrompt;
            selectedQuickPrompt = EditorGUILayout.Popup(L("Hazir gorev", "Quick task"), selectedQuickPrompt, quickPrompts);
            if (selectedQuickPrompt != previousQuickPrompt) prompt = quickPrompts[selectedQuickPrompt];
            GUILayout.Label(L("Tek talimat", "Single instruction"), SmallLabelStyle());
            var instructionRect = GUILayoutUtility.GetRect(GUIContent.none, EditorStyles.textArea, GUILayout.MinHeight(148f), GUILayout.ExpandWidth(true));
            HandleReferenceInput(instructionRect, true);
            prompt = EditorGUI.TextArea(instructionRect, prompt, EditorStyles.textArea);
            DrawReferenceDropZone();
            GUILayout.Space(6f);
            modelModeIndex = 0;
            GUILayout.Label(L("Yonlendirme: otomatik uzman agi", "Routing: automatic specialist network"), SmallLabelStyle());
            fullAutonomy = EditorGUILayout.ToggleLeft(L("Tam otonom (HIGH risk haric)", "Full autonomy (except HIGH risk)"), fullAutonomy);
            maxRepairAttempts = EditorGUILayout.IntSlider(L("Duzeltme", "Repairs"), maxRepairAttempts, 1, 3);
            var localModelStatus = LocalModelDownloadMonitor.Current;
            var modelMessageType = localModelStatus.State == LocalModelDownloadState.Ready
                ? MessageType.Info
                : localModelStatus.State == LocalModelDownloadState.Downloading ? MessageType.Warning : MessageType.None;
            EditorGUILayout.HelpBox(localModelStatus.Message, modelMessageType);
            if (GUILayout.Button(L("Durumu yenile", "Refresh status"), SecondaryButtonStyle(), GUILayout.Height(22f)))
            {
                LocalModelDownloadMonitor.Refresh();
                Repaint();
            }
            GUILayout.Space(8f);
            GUI.enabled = !isRunning && !AutonomousJobRunner.IsBusy && !string.IsNullOrWhiteSpace(prompt);
            if (GUILayout.Button(isRunning ? L("Uzmanlar birlikte calisiyor...", "Specialists are collaborating...") : L("Istedigi planla ve uzmanlara yonlendir", "Plan request and route to specialists"), PrimaryButtonStyle(), GUILayout.Height(32f))) SendPlanRequest();
            GUI.enabled = true;
            GUI.enabled = !isRunning && !AutonomousJobRunner.IsBusy && pendingChangeSet != null;
            if (GUILayout.Button(L("Onayla ve otonom uygula", "Approve and apply autonomously"), SecondaryButtonStyle(), GUILayout.Height(28f))) ApplyPendingChangeSet();
            GUI.enabled = true;
            GUILayout.Label(L("OTONOM IS", "AUTONOMOUS JOB"), SmallLabelStyle());
            GUILayout.Label(AutonomousJobRunner.LastStatus, MutedStyle());
            GUI.enabled = !AutonomousJobRunner.IsBusy;
            if (GUILayout.Button(L("Son islemi geri al", "Roll back last"), SecondaryButtonStyle(), GUILayout.Height(22f))) RollbackLastJob();
            GUI.enabled = true;
            GUILayout.Space(12f);
            GUILayout.Label(L("YANIT ONIZLEME", "RESPONSE PREVIEW"), SmallLabelStyle());
            responseScroll = EditorGUILayout.BeginScrollView(responseScroll, EditorStyles.helpBox, GUILayout.MinHeight(180f), GUILayout.MaxHeight(320f), GUILayout.ExpandHeight(true));
            var responseStyle = new GUIStyle(EditorStyles.wordWrappedLabel) { wordWrap = true };
            var responseWidth = Mathf.Max(180f, position.width - 470f);
            var responseHeight = Mathf.Max(150f, responseStyle.CalcHeight(new GUIContent(lastResponse ?? string.Empty), responseWidth));
            EditorGUILayout.SelectableLabel(lastResponse ?? string.Empty, responseStyle, GUILayout.MinHeight(responseHeight), GUILayout.ExpandWidth(true));
            EditorGUILayout.EndScrollView();
            EditorGUILayout.EndScrollView();
            EditorGUILayout.EndVertical();
        }

        private void DrawInspector()
        {
            var inspector = new GUIStyle(EditorStyles.helpBox) { padding = new RectOffset(12, 12, 12, 12) };
            inspector.normal.background = InspectorTexture;
            EditorGUILayout.BeginVertical(inspector, GUILayout.Width(250f), GUILayout.ExpandHeight(true));
            GUILayout.Label(L("PLAN GUVENLIKLERI", "PLAN GUARDRAILS"), SectionStyle());
            DrawCheck(L("Gorsel kanit", "Visual evidence"), L("Gorsel analiz incelenebilir kalir", "Image analysis stays reviewable"));
            DrawCheck(L("Unity bilgisi", "Unity knowledge"), L("URP ve proje baglami kontrol edilir", "URP and project context checked"));
            DrawCheck(L("Muhendislik elestirisi", "Critique"), L("Risk ve alternatifler once gosterilir", "Risk and alternatives shown first"));
            DrawCheck(L("Varlik uretimi", "Asset generation"), L("Flux Sprite'lari ayni guvenli is hatti ile uretilir", "Flux Sprites use the same guarded job pipeline"));
            GUILayout.Space(14f);
            GUILayout.Label(L("DURUM", "STATUS"), SmallLabelStyle());
            EditorGUILayout.HelpBox(status, isRunning ? MessageType.Info : MessageType.None);
            GUILayout.Space(8f);
            GUILayout.Label(L("SISTEM", "SYSTEM"), SmallLabelStyle());
            DrawCheck(L("Orkestrasyon", "Orchestration"), L("Planlama, kod ve varlik uzmanlari tek istek icin birlikte calisir", "Planning, code and asset specialists collaborate on one request"));
            DrawCheck(L("Yerel motor", "Local engine"), ServerManager.IsRunning ? L("Hazir", "Ready") : L("Istekle birlikte baslatilir", "Starts with the request"));
            GUILayout.Space(8f);
            GUILayout.Label(L("Teknik ayarlar ve hesap baglantilari AI Engineer menusunde bulunur.", "Technical settings and account connections are available from the AI Engineer menu."), MutedStyle());
            GUILayout.FlexibleSpace();
            EditorGUILayout.EndVertical();
        }

        private void DrawFluxAssetPanel()
        {
            var hasReference = !string.IsNullOrWhiteSpace(referenceImagePath);
            GUILayout.Space(12f);
            GUILayout.Label("FLUX.2 KLEIN 4B " + L("GORSEL VARLIK", "IMAGE ASSET"), SectionStyle());
            EditorGUILayout.HelpBox(
                L("ComfyUI/Flux ayni Control Center akisinin parcasidir. Uretilen PNG yedekli islemle Unity'ye yazilir ve Sprite olarak ice aktarilir.",
                    "ComfyUI/Flux is part of this Control Center flow. The PNG is written through a backed-up job and imported into Unity as a Sprite."),
                ServerManager.FluxIsRunning ? MessageType.Info : MessageType.Warning);
            DrawReferenceDropZone();
            GUILayout.Label(L("Gorsel talimati", "Image instruction"), SmallLabelStyle());
            imagePrompt = EditorGUILayout.TextArea(imagePrompt, EditorStyles.textArea, GUILayout.MinHeight(48f));
            EditorGUILayout.BeginHorizontal();
            GUILayout.Label(L("Dosya adi", "File name"), GUILayout.Width(72f));
            imageOutputName = EditorGUILayout.TextField(imageOutputName);
            GUILayout.Label(L("Boyut", "Size"), GUILayout.Width(42f));
            imageSizeIndex = EditorGUILayout.Popup(imageSizeIndex, new[] { "512 x 512", "1024 x 1024" }, GUILayout.Width(104f));
            EditorGUILayout.EndHorizontal();
            if (hasReference)
            {
                EditorGUILayout.BeginHorizontal();
                GUILayout.Label(L("Duzeltme gucu", "Edit strength"), GUILayout.Width(92f));
                imageEditStrength = EditorGUILayout.Slider(imageEditStrength, 0.05f, 1f);
                GUILayout.Label(imageEditStrength.ToString("0.00"), GUILayout.Width(34f));
                EditorGUILayout.EndHorizontal();
            }
            EditorGUILayout.BeginHorizontal();
            GUI.enabled = !isRunning && !AutonomousJobRunner.IsBusy && !string.IsNullOrWhiteSpace(imagePrompt);
            if (GUILayout.Button(L("Flux ile Sprite uret ve Unity'ye aktar", "Generate Sprite with Flux and import into Unity"), PrimaryButtonStyle(), GUILayout.Height(34f)))
                StartFluxImageGeneration();
            GUI.enabled = true;
            if (GUILayout.Button(ServerManager.FluxIsRunning ? L("Flux hazir", "Flux ready") : L("Flux motorunu baslat", "Start Flux engine"), GUILayout.Width(140f), GUILayout.Height(34f)))
            {
                ServerManager.Start();
                ServerManager.StartFluxEngine();
                status = L("Flux motoru baslatiliyor; hazir oldugunda ayni dugmeden Sprite uretebilirsiniz.", "Flux engine is starting; generate a Sprite from this same button when it is ready.");
            }
            EditorGUILayout.EndHorizontal();
        }

        private void DrawReferenceDropZone()
        {
            GUILayout.Space(5f);
            var hasReference = !string.IsNullOrWhiteSpace(referenceImagePath);
            var label = hasReference
                ? L("Referans: ", "Reference: ") + referenceImagePath
                : L("Referans gorsel ekle: herhangi bir ekran goruntusu, fotograf veya konsept. Surukle-birak ya da Ctrl+V kullan.", "Add a reference image: any screenshot, photo, or concept. Drag and drop or use Ctrl+V.");
            var dropZone = GUILayoutUtility.GetRect(10f, 46f, GUILayout.ExpandWidth(true));
            GUI.Box(dropZone, label, EditorStyles.helpBox);
            HandleReferenceInput(dropZone, true);
            if (GUILayout.Button(L("Gorsel sec (veya Ctrl+V kullan)", "Choose image (or use Ctrl+V)"), SecondaryButtonStyle(), GUILayout.Height(22f))) ChooseReferenceImage();
            if (hasReference && GUILayout.Button(L("Referansi temizle", "Clear reference"), SecondaryButtonStyle(), GUILayout.Height(20f))) referenceImagePath = string.Empty;
        }

        private void HandleReferenceInput(Rect targetArea, bool captureClipboard)
        {
            var current = Event.current;
            if (targetArea.Contains(current.mousePosition))
            {
                if (current.type == EventType.DragUpdated || current.type == EventType.DragPerform)
                {
                    DragAndDrop.visualMode = DragAndDropVisualMode.Copy;
                    if (current.type == EventType.DragPerform)
                    {
                        DragAndDrop.AcceptDrag();
                        var path = DragAndDrop.paths != null && DragAndDrop.paths.Length > 0 ? DragAndDrop.paths[0] : string.Empty;
                        if (string.IsNullOrWhiteSpace(path) && DragAndDrop.objectReferences.Length > 0)
                            path = AssetDatabase.GetAssetPath(DragAndDrop.objectReferences[0]);
                        ImportReferenceImage(path);
                    }
                    current.Use();
                }
            }
            if (captureClipboard && current.type == EventType.KeyDown && current.control && current.keyCode == KeyCode.V && ClipboardLikelyHasReferenceImage())
            {
                TryPasteReferenceImage();
                current.Use();
            }
        }

        private static bool ClipboardLikelyHasReferenceImage()
        {
            var clipboard = (EditorGUIUtility.systemCopyBuffer ?? string.Empty).Trim().Trim('"');
            if (clipboard.StartsWith("file:///", StringComparison.OrdinalIgnoreCase)) clipboard = new Uri(clipboard).LocalPath;
            // Image-only clipboard content does not expose text to Unity; ordinary text
            // remains available for normal Ctrl+V into the instruction field.
            return string.IsNullOrWhiteSpace(clipboard) || File.Exists(clipboard);
        }

        private void TryPasteReferenceImage()
        {
            var clipboard = (EditorGUIUtility.systemCopyBuffer ?? string.Empty).Trim().Trim('"');
            if (clipboard.StartsWith("file:///", StringComparison.OrdinalIgnoreCase)) clipboard = new Uri(clipboard).LocalPath;
            if (File.Exists(clipboard))
            {
                ImportReferenceImage(clipboard);
                return;
            }
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
            var assetPath = CreateReferenceAssetPath(projectRoot, "ClipboardReference.png");
            var output = Path.Combine(projectRoot, assetPath);
            Directory.CreateDirectory(Path.GetDirectoryName(output) ?? projectRoot);
            var escapedPath = output.Replace("'", "''");
            var command = "Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; if ([Windows.Forms.Clipboard]::ContainsImage()) { [Windows.Forms.Clipboard]::GetImage().Save('" + escapedPath + "', [Drawing.Imaging.ImageFormat]::Png) }";
            try
            {
                using var process = Process.Start(new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    Arguments = "-NoProfile -STA -Command \"" + command + "\"",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                });
                process?.WaitForExit(5000);
                AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
                if (File.Exists(output))
                {
                    referenceImagePath = assetPath;
                    status = L("Pano gorseli referans olarak alindi.", "Clipboard image imported as the reference.");
                }
                else status = L("Panoda resim veya resim dosya yolu bulunamadi.", "No image or image-file path was found on the clipboard.");
            }
            catch (Exception error) { status = L("Pano gorseli alinamadi: ", "Clipboard image could not be imported: ") + error.Message; }
        }

        private void ImportReferenceImage(string sourcePath)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(sourcePath)) return;
                if (Directory.Exists(sourcePath))
                {
                    status = L("Klasor degil, bir PNG/JPG/WEBP dosyasi birakin veya secin.", "Drop or choose a PNG/JPG/WEBP file, not a folder.");
                    return;
                }
                var normalized = sourcePath.Replace('\\', '/');
                if (normalized.StartsWith("Assets/", StringComparison.OrdinalIgnoreCase))
                {
                    referenceImagePath = normalized;
                    status = L("Proje gorseli tek istege referans olarak eklendi.", "Project image added as reference to the single request.");
                    return;
                }
                if (!File.Exists(sourcePath)) { status = L("Referans gorsel bulunamadi.", "Reference image was not found."); return; }
                var extension = Path.GetExtension(sourcePath).ToLowerInvariant();
                if (extension != ".png" && extension != ".jpg" && extension != ".jpeg" && extension != ".webp")
                {
                    status = L("Referans PNG, JPG, JPEG veya WEBP olmali.", "Reference must be PNG, JPG, JPEG or WEBP.");
                    return;
                }
                var projectRoot = Directory.GetParent(Application.dataPath)?.FullName ?? Directory.GetCurrentDirectory();
                var assetPath = CreateReferenceAssetPath(projectRoot, Path.GetFileName(sourcePath));
                var target = Path.Combine(projectRoot, assetPath);
                Directory.CreateDirectory(Path.GetDirectoryName(target) ?? projectRoot);
                File.Copy(sourcePath, target, false);
                AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
                referenceImagePath = assetPath;
                status = L("Referans gorsel projeye alindi; ilgili uzmanlara otomatik baglam olarak verilecek.", "Reference image imported into the project; it will be passed as context to the relevant specialists automatically.");
                Repaint();
            }
            catch (Exception error)
            {
                status = L("Referans gorsel alinamadi: ", "Reference image could not be imported: ") + error.Message;
                UnityEngine.Debug.LogError("[AI] " + status);
            }
        }

        private static string CreateReferenceAssetPath(string projectRoot, string fileName)
        {
            const string folder = "Assets/AIEngineerGenerated/References";
            var absoluteFolder = Path.Combine(projectRoot, "Assets", "AIEngineerGenerated", "References");
            Directory.CreateDirectory(absoluteFolder);
            var extension = Path.GetExtension(fileName).ToLowerInvariant();
            if (extension != ".png" && extension != ".jpg" && extension != ".jpeg" && extension != ".webp") extension = ".png";
            var baseName = Path.GetFileNameWithoutExtension(fileName);
            baseName = new string((baseName ?? string.Empty).Where(character => char.IsLetterOrDigit(character) || character == '_' || character == '-').ToArray());
            if (string.IsNullOrWhiteSpace(baseName)) baseName = "Reference";
            return folder + "/" + baseName + "_" + Guid.NewGuid().ToString("N").Substring(0, 10) + extension;
        }

        private void StartFluxImageGeneration()
        {
            ServerManager.Start();
            if (!ServerManager.FluxIsRunning)
            {
                status = L("Flux motoru henuz hazir degil. Model yuklenirken birkac saniye bekleyip tekrar deneyin.", "Flux engine is not ready yet. Wait a few seconds for models to load, then try again.");
                return;
            }
            var rawName = Path.GetFileNameWithoutExtension(imageOutputName ?? string.Empty);
            var safeName = new string((rawName ?? string.Empty).ToCharArray().Where(character => char.IsLetterOrDigit(character) || character == '_' || character == '-').ToArray());
            if (string.IsNullOrWhiteSpace(safeName)) safeName = "GeneratedSprite";
            var size = imageSizeIndex == 0 ? 512 : 1024;
            var outputPath = "Assets/AIEngineerGenerated/Textures/" + safeName + ".png";
            var changeSet = new AutonomousChangeSet
            {
                protocol = "ai-engineer.change-set/v1",
                requestId = "flux-" + Guid.NewGuid().ToString("N"),
                summary = L("Flux.2 ile Sprite uret ve Unity'ye aktar: ", "Generate and import a Sprite with Flux.2: ") + safeName,
                risk = "LOW",
                requiresConfirmation = false,
                operations = new[]
                {
                    new AutonomousChangeOperation
                    {
                        id = "generate-image",
                        kind = "generate_image",
                        prompt = imagePrompt.Trim(),
                        sourceImagePath = referenceImagePath,
                        editStrength = imageEditStrength,
                        outputPath = outputPath,
                        width = size,
                        height = size,
                        transparent = false,
                        importType = "Sprite",
                        overwrite = false,
                    },
                },
                validation = new AutonomousValidation { compile = false, playMode = false, checks = Array.Empty<string>() },
                explanation = new[] { string.IsNullOrWhiteSpace(referenceImagePath) ? L("PNG Flux.2 ile uretilecek, yedeklenecek ve Sprite olarak ice aktarilacak.", "The PNG will be generated with Flux.2, backed up, and imported as a Sprite.") : L("Referans gorsel Flux.2 ile talimata gore duzenlenecek, yedeklenecek ve Sprite olarak ice aktarilacak.", "The reference image will be edited by Flux.2 according to the instruction, backed up, and imported as a Sprite.") },
                warnings = new[] { L("Kurulu Flux akisi su an opak PNG uretir; saydamlik sonraki varlik-isleme adimidir.", "The installed Flux workflow currently produces opaque PNGs; alpha processing is the next asset-processing step.") },
                model = "flux-2-klein-4b",
                responseType = "change_set",
                answer = string.Empty,
            };
            status = L("Flux Sprite isi kuyruga alindi; yedekleme ve Unity ice aktarma otomatik ilerleyecek.", "Flux Sprite job queued; backup and Unity import will continue automatically.");
            lastResponse = AutonomousChangeSetFormatter.Format(changeSet);
            EditorApplication.delayCall += () => StartQueuedChangeSet(imagePrompt, string.Empty, "local", changeSet, 0);
            Repaint();
        }

        private async void SendPlanRequest()
        {
            isRunning = true;
            status = L("Istek ve mevcut Unity baglami hazirlaniyor...", "Preparing the request and current Unity context...");
            Repaint();
            try
            {
                var modelMode = SelectedModelMode();
                var response = await AutonomousRequestSender.Plan(prompt, referenceImagePath, modelMode);
                if (response.IsAnswer)
                {
                    pendingChangeSet = null;
                    status = L("Yerel model proje baglami ve Unity belgelerine dayanarak yanitladi.", "The local model answered using project context and Unity documentation.");
                    lastResponse = response.answer;
                    return;
                }
                if (!response.IsValid)
                    throw new InvalidDataException("Backend returned a plan that cannot be applied. Generate the plan again.");
                pendingChangeSet = response;
                status = modelMode == "local"
                    ? L("Qwen planladi, Qwen Coder uygulanabilir degisiklik setini hazirladi; gereken gorsel varliklar Flux'a otomatik yonlendirilecek.", "Qwen planned, Qwen Coder prepared the executable change set; required image assets will be routed to Flux automatically.")
                    : L("Secilen hesap saglayicisi uygulanabilir degisiklik seti uretti.", "The selected account provider produced an executable change set.");
                lastResponse = AutonomousChangeSetFormatter.Format(pendingChangeSet);
                if (fullAutonomy && !string.Equals(pendingChangeSet.risk, "HIGH", StringComparison.OrdinalIgnoreCase))
                    StartPendingChangeSet();
            }
            catch (Exception error)
            {
                status = L("Istek guvenli sekilde durduruldu: ", "Request stopped safely: ") + error.Message;
                lastResponse = error.ToString();
            }
            finally { isRunning = false; Repaint(); }
        }

        private void ApplyPendingChangeSet()
        {
            if (pendingChangeSet == null) return;
            if (!pendingChangeSet.IsValid)
            {
                status = L("Plan eksik veya gecersiz; yeniden plan olusturun.", "The plan is incomplete or invalid; generate it again.");
                pendingChangeSet = null;
                Repaint();
                return;
            }
            var approved = EditorUtility.DisplayDialog(
                "AI Engineer",
                L("Degisiklik seti yedek alacak, projeyi degistirecek, derleyecek ve hata varsa en fazla belirlenen sayida kendi kendine duzeltecek. Devam edilsin mi?", "The change set will create a backup, modify the project, compile it and self-repair up to the selected limit. Continue?"),
                L("Uygula", "Apply"),
                L("Vazgec", "Cancel"));
            if (!approved) return;
            StartPendingChangeSet();
        }

        private void StartPendingChangeSet()
        {
            if (pendingChangeSet == null) return;
            if (!pendingChangeSet.IsValid)
            {
                status = L("Plan uygulanamiyor; eksik degisiklik seti yeniden olusturulmeli.", "The plan cannot be applied; the incomplete change set must be generated again.");
                pendingChangeSet = null;
                Repaint();
                return;
            }
            var changeSet = pendingChangeSet;
            var requestPrompt = prompt;
            var requestImage = referenceImagePath;
            var requestModel = SelectedModelMode();
            var repairs = maxRepairAttempts;
            pendingChangeSet = null;
            status = L("Otonom is kuyruga alindi; Unity GUI turu tamamlaninca baslayacak.", "The autonomous job is queued and will start after the current Unity GUI pass.");
            lastResponse += "\n\n" + L("OTONOM UYGULAMA BASLATILDI", "AUTONOMOUS APPLY STARTED");
            EditorApplication.delayCall += () => StartQueuedChangeSet(requestPrompt, requestImage, requestModel, changeSet, repairs);
            Repaint();
        }

        private void StartQueuedChangeSet(string requestPrompt, string requestImage, string requestModel, AutonomousChangeSet changeSet, int repairs)
        {
            try
            {
                if (changeSet == null || !changeSet.IsValid)
                    throw new ArgumentException("A valid change set is required.");
                AutonomousJobRunner.Start(requestPrompt, requestImage, requestModel, changeSet, repairs);
                status = L("Otonom is baslatildi. Dosya yedegi, derleme, dogrulama ve gerekirse duzeltme otomatik ilerleyecek.", "Autonomous job started. Backup, compilation, validation and repair will continue automatically.");
            }
            catch (Exception error)
            {
                status = L("Otonom is baslatilamadi: ", "Autonomous job could not start: ") + error.Message;
                lastResponse += "\n\n" + status;
                Debug.LogError("[AI Autonomous] " + status);
            }
            Repaint();
        }

        private void RollbackLastJob()
        {
            if (AutonomousJobRunner.RollbackLast(out var message))
            {
                status = message;
                lastResponse += "\n\n" + message;
            }
            else status = message;
        }

        private void ChooseReferenceImage()
        {
            var selected = EditorUtility.OpenFilePanel(L("Herhangi bir referans gorsel sec", "Choose any reference image"), string.Empty, "png,jpg,jpeg,webp");
            if (!string.IsNullOrWhiteSpace(selected)) ImportReferenceImage(selected);
        }

        private void ChooseProviderExecutable(bool qwen)
        {
            var selected = EditorUtility.OpenFilePanel(
                qwen ? L("Qwen Code calistirilabilir dosyasini sec", "Choose Qwen Code executable") : L("Codex calistirilabilir dosyasini sec", "Choose Codex executable"),
                string.Empty,
                "exe");
            if (string.IsNullOrWhiteSpace(selected)) return;
            if (qwen) ProviderSetupManager.QwenExecutable = selected;
            else ProviderSetupManager.CodexExecutable = selected;
            ServerManager.Restart();
            status = L("Saglayici yolu kaydedildi ve backend yeniden baslatildi.", "Provider path saved and backend restarted.");
        }

        private string SelectedModelMode()
        {
            return modelModeIndex switch
            {
                1 => "qwen_code",
                2 => "codex",
                3 => "cloud",
                _ => "local",
            };
        }

        private static void DrawCheck(string title, string detail)
        {
            var check = new GUIStyle(EditorStyles.label);
            check.normal.textColor = new Color(0.35f, 0.83f, 0.66f);
            GUILayout.Label("● " + title, check);
            GUILayout.Label("   " + detail, MutedStyle());
            GUILayout.Space(5f);
        }

        private string SectionHint()
        {
            return activeSection switch
            {
                0 => L("Acik bir istekten kapsamli bir Unity plani veya mobil oyun giris UI'i olustur.", "Create a scoped Unity plan or a mobile game entrance UI from a clear request."),
                1 => L("Degisiklikten once sahne, script, gorsel veya proje yapisini incele.", "Inspect a scene, script, image or project structure before editing."),
                _ => L("Sorunlari bul, geri alinabilir onarimlar oner ve sonucu dogrula.", "Find issues, propose reversible repairs and validate the outcome."),
            };
        }

        private static GUIStyle TitleStyle() { var style = new GUIStyle(EditorStyles.boldLabel) { fontSize = 22 }; style.normal.textColor = new Color(0.88f, 0.95f, 1f); return style; }
        private static GUIStyle SectionStyle() { var style = new GUIStyle(EditorStyles.boldLabel) { fontSize = 13 }; style.normal.textColor = new Color(0.58f, 0.84f, 1f); return style; }
        private static GUIStyle SmallLabelStyle() { var style = new GUIStyle(EditorStyles.miniBoldLabel); style.normal.textColor = new Color(0.62f, 0.7f, 0.78f); return style; }
        private static GUIStyle MutedStyle() { var style = new GUIStyle(EditorStyles.miniLabel) { wordWrap = true }; style.normal.textColor = new Color(0.58f, 0.64f, 0.7f); return style; }
        private static GUIStyle StatusStyle(bool online) { var style = new GUIStyle(EditorStyles.miniBoldLabel); style.normal.textColor = online ? new Color(0.35f, 0.83f, 0.66f) : new Color(1f, 0.72f, 0.28f); return style; }
        private static GUIStyle PrimaryButtonStyle()
        {
            var style = new GUIStyle(GUI.skin.button) { fontStyle = FontStyle.Bold, fixedHeight = 32f };
            style.normal.background = PrimaryButtonTexture; style.hover.background = ActiveButtonTexture;
            style.normal.textColor = new Color(0.9f, 0.98f, 1f); return style;
        }

        private static GUIStyle SecondaryButtonStyle()
        {
            var style = new GUIStyle(GUI.skin.button) { fontSize = 11, padding = new RectOffset(9, 9, 3, 3) };
            style.normal.background = SecondaryButtonTexture; style.hover.background = ActiveButtonTexture;
            style.normal.textColor = new Color(0.72f, 0.86f, 0.94f); return style;
        }

        private static void EnsureTextures()
        {
            if (HeaderTexture == null) HeaderTexture = MakeTexture(new Color(0.045f, 0.09f, 0.16f));
            if (SidebarTexture == null) SidebarTexture = MakeTexture(new Color(0.075f, 0.09f, 0.13f));
            if (InspectorTexture == null) InspectorTexture = MakeTexture(new Color(0.065f, 0.08f, 0.11f));
            if (PrimaryButtonTexture == null) PrimaryButtonTexture = MakeTexture(new Color(0.08f, 0.37f, 0.56f));
            if (SecondaryButtonTexture == null) SecondaryButtonTexture = MakeTexture(new Color(0.12f, 0.17f, 0.23f));
            if (ActiveButtonTexture == null) ActiveButtonTexture = MakeTexture(new Color(0.11f, 0.47f, 0.68f));
        }

        private static Texture2D MakeTexture(Color color)
        {
            var texture = new Texture2D(1, 1) { hideFlags = HideFlags.HideAndDontSave };
            texture.SetPixel(0, 0, color);
            texture.Apply();
            return texture;
        }

        private static string ShortPath(string path)
        {
            return path.Length <= 34 ? path : "..." + path.Substring(path.Length - 31);
        }

        private static string L(string turkish, string english) => AIEngineerLocalization.Text(turkish, english);

        private static string FormatWorkflow(string response)
        {
            try
            {
                var workflow = AIEngineer.Runtime.JsonWorkflowLoader.Load(response);
                if (workflow?.tasks == null || workflow.tasks.Count == 0) return response;
                var output = new StringBuilder();
                output.AppendLine(L("PLAN HAZIR", "PLAN READY"));
                output.AppendLine(workflow.workflow ?? "AI Workflow");
                output.AppendLine();
                for (var index = 0; index < workflow.tasks.Count; index++)
                {
                    var task = workflow.tasks[index];
                    output.Append(index + 1).Append(". ").Append(ReadableAction(task.action));
                    if (!string.IsNullOrWhiteSpace(task.target)) output.Append(" -> ").Append(task.target);
                    output.AppendLine();
                }
                output.AppendLine();
                output.Append(L("Bu bir onizleme planidir; otomatik uygulanmadi.", "This is a preview plan; it was not applied automatically."));
                return output.ToString();
            }
            catch
            {
                return response;
            }
        }

        private static string ReadableAction(string action)
        {
            return action switch
            {
                "FindObject" => L("Nesneyi bul", "Find object"),
                "FindPrefab" => L("Prefab'i bul", "Find prefab"),
                "Instantiate" => L("Nesne olustur", "Instantiate object"),
                "SetParent" => L("Ust nesneyi ayarla", "Set parent"),
                "ResetTransform" => L("Transform'u sifirla", "Reset transform"),
                "Destroy" => L("Nesneyi kaldir", "Remove object"),
                _ => string.IsNullOrWhiteSpace(action) ? L("Islem", "Action") : action,
            };
        }

        private static void OpenUserGuide()
        {
            const string path = "Assets/AIEngineer/CONTROL_CENTER_KULLANIM_KILAVUZU.md";
            var guide = AssetDatabase.LoadAssetAtPath<TextAsset>(path);
            if (guide == null)
            {
                EditorUtility.DisplayDialog("AI Engineer", L("Kullanim kilavuzu bulunamadi.", "User guide was not found."), "OK");
                return;
            }
            Selection.activeObject = guide;
            EditorGUIUtility.PingObject(guide);
            AssetDatabase.OpenAsset(guide);
        }
    }
}
