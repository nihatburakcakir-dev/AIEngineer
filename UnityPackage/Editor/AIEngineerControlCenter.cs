using System;
using System.IO;
using System.Text;
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
            if (string.IsNullOrWhiteSpace(prompt)) prompt = AIEngineerLocalization.DefaultPrompt;
            if (string.IsNullOrWhiteSpace(status)) status = L("Hazir. Bir istek yazin veya hazir gorev secin.", "Ready. Enter a request or choose a quick task.");
            if (string.IsNullOrWhiteSpace(lastResponse)) lastResponse = L("Henuz bir yanit yok.", "No response yet.");
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
            EditorGUILayout.BeginVertical(sidebar, GUILayout.Width(154f), GUILayout.ExpandHeight(true));
            var sections = AIEngineerLocalization.Sections;
            GUILayout.Label(L("CALISMA ALANI", "WORKSPACE"), SmallLabelStyle());
            GUILayout.Space(8f);
            for (var index = 0; index < sections.Length; index++)
            {
                var selected = activeSection == index;
                var button = new GUIStyle(EditorStyles.miniButton) { alignment = TextAnchor.MiddleLeft, fixedHeight = 34f };
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
            GUILayout.Label(L("Talimat", "Instruction"), SmallLabelStyle());
            prompt = EditorGUILayout.TextArea(prompt, EditorStyles.textArea, GUILayout.MinHeight(148f), GUILayout.ExpandHeight(false));
            GUILayout.Space(6f);
            EditorGUILayout.BeginHorizontal();
            modelModeIndex = EditorGUILayout.Popup(L("Model", "Model"), modelModeIndex, new[]
            {
                L("Yerel (30B / otonom)", "Local (30B / autonomous)"),
                L("Qwen (hesap > Codex)", "Qwen (account > Codex)"),
                L("Codex Plus (hesap > Qwen)", "Codex Plus (account > Qwen)"),
                L("Bulut (API anahtari)", "Cloud (API key)"),
            }, GUILayout.Width(260f));
            fullAutonomy = EditorGUILayout.ToggleLeft(L("Tam otonom (HIGH risk haric)", "Full autonomy (except HIGH risk)"), fullAutonomy, GUILayout.Width(220f));
            GUILayout.Label(L("Duzeltme", "Repairs"), GUILayout.Width(58f));
            maxRepairAttempts = EditorGUILayout.IntSlider(maxRepairAttempts, 1, 3, GUILayout.Width(150f));
            EditorGUILayout.EndHorizontal();
            var localModelStatus = LocalModelDownloadMonitor.Current;
            var modelMessageType = localModelStatus.State == LocalModelDownloadState.Ready
                ? MessageType.Info
                : localModelStatus.State == LocalModelDownloadState.Downloading ? MessageType.Warning : MessageType.None;
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.HelpBox(localModelStatus.Message, modelMessageType);
            if (GUILayout.Button(L("Model durumunu yenile", "Refresh model status"), GUILayout.Width(130f), GUILayout.Height(38f)))
            {
                LocalModelDownloadMonitor.Refresh();
                Repaint();
            }
            EditorGUILayout.EndHorizontal();
            EditorGUILayout.BeginHorizontal();
            GUILayout.Label(L("Referans gorsel", "Reference image"), GUILayout.Width(100f));
            EditorGUILayout.SelectableLabel(string.IsNullOrWhiteSpace(referenceImagePath) ? L("Secilmedi", "Not selected") : referenceImagePath, EditorStyles.textField, GUILayout.Height(20f));
            if (GUILayout.Button(L("Gorsel sec", "Choose image"), GUILayout.Width(92f))) ChooseReferenceImage();
            if (!string.IsNullOrWhiteSpace(referenceImagePath) && GUILayout.Button(L("Temizle", "Clear"), GUILayout.Width(60f))) referenceImagePath = string.Empty;
            EditorGUILayout.EndHorizontal();
            GUILayout.Space(8f);
            EditorGUILayout.BeginHorizontal();
            GUI.enabled = !isRunning && !AutonomousJobRunner.IsBusy && !string.IsNullOrWhiteSpace(prompt);
            if (GUILayout.Button(isRunning ? L("Yerel model dusunuyor...", "Local model is thinking...") : L("Yerel modele gonder", "Send to local model"), PrimaryButtonStyle(), GUILayout.Height(38f))) SendPlanRequest();
            GUI.enabled = true;
            if (GUILayout.Button(L("Yerel motoru baslat", "Start local engine"), GUILayout.Height(38f), GUILayout.Width(150f)))
            {
                ServerManager.Start();
                status = ServerManager.IsRunning
                    ? L("Yerel motor baslatildi.", "Local engine started.")
                    : L("Yerel motor baslatilamadi; Console kaydini kontrol edin.", "Local engine could not start; check the Console.");
            }
            EditorGUILayout.EndHorizontal();
            if (GUILayout.Button(L("Qwen / Codex hesabini bagla", "Connect Qwen / Codex account"), GUILayout.Height(26f)))
                AIEngineerProviderWindow.Open();
            GUI.enabled = !isRunning && !AutonomousJobRunner.IsBusy && pendingChangeSet != null;
            if (GUILayout.Button(L("Onayla ve otonom uygula", "Approve and apply autonomously"), GUILayout.Height(34f))) ApplyPendingChangeSet();
            GUI.enabled = true;
            EditorGUILayout.BeginHorizontal();
            GUILayout.Label(L("OTONOM IS", "AUTONOMOUS JOB"), SmallLabelStyle(), GUILayout.Width(90f));
            GUILayout.Label(AutonomousJobRunner.LastStatus, MutedStyle(), GUILayout.ExpandWidth(true));
            GUI.enabled = !AutonomousJobRunner.IsBusy;
            if (GUILayout.Button(L("Son islemi geri al", "Roll back last"), GUILayout.Width(125f))) RollbackLastJob();
            GUI.enabled = true;
            EditorGUILayout.EndHorizontal();
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
            DrawCheck(L("Hafiza", "Memory"), L("Ilgili gecmis dersler plana eklenir", "Relevant past lessons attached"));
            GUILayout.Space(14f);
            GUILayout.Label(L("DURUM", "STATUS"), SmallLabelStyle());
            EditorGUILayout.HelpBox(status, isRunning ? MessageType.Info : MessageType.None);
            GUILayout.Space(8f);
            GUILayout.Label(L("PAKET ICERIGI", "PACKAGE CONTENT"), SmallLabelStyle());
            GUILayout.Label(L("- Ana planlayici ve dogrulayicilar", "- Core planner and validators"), MutedStyle());
            GUILayout.Label(L("- Gorsel / karakter / oyun araclari", "- Image / character / game tools"), MutedStyle());
            GUILayout.Label(L("- Mobil marble-shooter ornegi", "- Mobile marble-shooter sample"), MutedStyle());
            GUILayout.Label(L("- Disari aktarilabilir Unity paketi", "- Exportable Unity package"), MutedStyle());
            GUILayout.Space(10f);
            GUILayout.Label(L("PYTHON BACKEND", "PYTHON BACKEND"), SmallLabelStyle());
            GUILayout.Label(ShortPath(ServerManager.BackendRoot), MutedStyle());
            if (GUILayout.Button(L("Backend klasorunu sec", "Choose backend folder"), GUILayout.Height(28f)))
            {
                var selected = EditorUtility.OpenFolderPanel(L("Cikartilan AI Engineer backend klasorunu sec", "Choose extracted AI Engineer backend"), ServerManager.BackendRoot, "");
                if (!string.IsNullOrWhiteSpace(selected)) ServerManager.BackendRoot = selected;
            }
            GUILayout.Space(6f);
            GUILayout.Label(L("PYTHON CALISTIRICI", "PYTHON EXECUTABLE"), SmallLabelStyle());
            GUILayout.Label(ShortPath(ServerManager.PythonExecutable), MutedStyle());
            if (GUILayout.Button(L("Python dosyasini sec", "Choose Python executable"), GUILayout.Height(28f)))
            {
                var selected = EditorUtility.OpenFilePanel(L("Python calistirilabilir dosyasini sec", "Choose Python executable"), System.IO.Path.GetDirectoryName(ServerManager.PythonExecutable) ?? string.Empty, "exe");
                if (!string.IsNullOrWhiteSpace(selected)) ServerManager.PythonExecutable = selected;
            }
            GUILayout.Space(8f);
            GUILayout.Label(L("MODEL SAGLAYICILARI", "MODEL PROVIDERS"), SmallLabelStyle());
            var qwenConnected = ProviderSetupManager.IsQwenProviderConfigured;
            EditorGUILayout.HelpBox(
                qwenConnected
                    ? L("Qwen hesabi etkin: ", "Qwen account active: ") + ProviderSetupManager.QwenProviderStatus
                    : L("Qwen.ai Gmail oturumu tek basina Code'u etkinlestirmez. Guvenli tarayici girisini baslatin.", "A Qwen.ai Gmail session alone does not activate Code. Start the secure browser sign-in."),
                qwenConnected ? MessageType.Info : MessageType.Warning);
            if (GUILayout.Button(L("Qwen hesabini bagla (tarayici)", "Connect Qwen account (browser)"), GUILayout.Height(28f)))
            {
                ProviderSetupManager.OpenQwenAccountSignIn();
                status = L("Qwen tarayici ve terminal akisi acildi. Giris sonrasi terminalde /auth ile saglayiciyi tamamlayin.", "Qwen browser and terminal flow opened. Finish the provider with /auth after sign-in.");
            }
            if (GUILayout.Button(L("Qwen Code terminalini ac", "Open Qwen Code terminal"), GUILayout.Height(26f))) ProviderSetupManager.OpenQwenSetup();
            if (GUILayout.Button(L("Qwen baglantisini kontrol et", "Check Qwen connection"), GUILayout.Height(24f)))
                status = ProviderSetupManager.IsQwenProviderConfigured
                    ? L("Qwen baglantisi etkin: ", "Qwen connection active: ") + ProviderSetupManager.QwenProviderStatus
                    : L("Qwen baglantisi bulunamadi. Tarayici girisini acin ve terminalde /auth kullanin.", "No Qwen connection found. Open browser sign-in and use /auth in the terminal.");
            if (GUILayout.Button(L("Codex Plus girisini ac", "Open Codex Plus login"), GUILayout.Height(26f))) ProviderSetupManager.OpenCodexLogin();
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button(L("Qwen yolunu sec", "Choose Qwen path"), GUILayout.Height(24f))) ChooseProviderExecutable(true);
            if (GUILayout.Button(L("Codex yolunu sec", "Choose Codex path"), GUILayout.Height(24f))) ChooseProviderExecutable(false);
            EditorGUILayout.EndHorizontal();
            GUILayout.Space(8f);
            if (GUILayout.Button(L("Kullanim kilavuzunu ac", "Open user guide"), GUILayout.Height(30f))) OpenUserGuide();
            GUILayout.FlexibleSpace();
            if (GUILayout.Button(L("Console'u ac", "Open Console"), GUILayout.Height(28f))) EditorApplication.ExecuteMenuItem("Window/General/Console");
            EditorGUILayout.EndVertical();
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
                    ? L("Yerel model uygulanabilir degisiklik seti uretti; yedek, derleme ve geri alma korumalari etkin.", "Local model produced an executable change set; backup, compilation and rollback safeguards are enabled.")
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
            var selected = EditorUtility.OpenFilePanel(L("Referans oyun veya karakter gorseli sec", "Choose a game or character reference image"), string.Empty, "png,jpg,jpeg");
            if (!string.IsNullOrWhiteSpace(selected)) referenceImagePath = selected;
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
                2 => L("Sorunlari bul, geri alinabilir onarimlar oner ve sonucu dogrula.", "Find issues, propose reversible repairs and validate the outcome."),
                3 => L("Asamali Unity istegiyle oyun prototipi, ozellik veya oyuncuya oyunu anlatan giris ekrani uret.", "Generate a game prototype, feature, or an entrance screen that explains the game to the player."),
                _ => L("Gecmis dersleri ve muhendislik kisitlarini yeni plana tasi.", "Bring relevant lessons and engineering constraints into the next plan."),
            };
        }

        private static GUIStyle TitleStyle() { var style = new GUIStyle(EditorStyles.boldLabel) { fontSize = 22 }; style.normal.textColor = new Color(0.88f, 0.95f, 1f); return style; }
        private static GUIStyle SectionStyle() { var style = new GUIStyle(EditorStyles.boldLabel) { fontSize = 13 }; style.normal.textColor = new Color(0.58f, 0.84f, 1f); return style; }
        private static GUIStyle SmallLabelStyle() { var style = new GUIStyle(EditorStyles.miniBoldLabel); style.normal.textColor = new Color(0.62f, 0.7f, 0.78f); return style; }
        private static GUIStyle MutedStyle() { var style = new GUIStyle(EditorStyles.miniLabel) { wordWrap = true }; style.normal.textColor = new Color(0.58f, 0.64f, 0.7f); return style; }
        private static GUIStyle StatusStyle(bool online) { var style = new GUIStyle(EditorStyles.miniBoldLabel); style.normal.textColor = online ? new Color(0.35f, 0.83f, 0.66f) : new Color(1f, 0.72f, 0.28f); return style; }
        private static GUIStyle PrimaryButtonStyle() { var style = new GUIStyle(GUI.skin.button) { fontStyle = FontStyle.Bold }; style.normal.textColor = new Color(0.62f, 0.9f, 1f); return style; }

        private static void EnsureTextures()
        {
            if (HeaderTexture == null) HeaderTexture = MakeTexture(new Color(0.045f, 0.09f, 0.16f));
            if (SidebarTexture == null) SidebarTexture = MakeTexture(new Color(0.075f, 0.09f, 0.13f));
            if (InspectorTexture == null) InspectorTexture = MakeTexture(new Color(0.065f, 0.08f, 0.11f));
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
