import json
import tempfile
import unittest
from pathlib import Path


class UnityPackageDeliveryTests(unittest.TestCase):
    def test_package_metadata_identifies_complete_release(self):
        package = json.loads(Path("UnityPackage/package.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(package["name"], "com.aiengineer.core")
        self.assertEqual(package["version"], "0.3.0")
        self.assertIn("mobile marble-shooter", package["description"])

    def test_control_center_has_clear_original_unity_workflow(self):
        source = Path("UnityPackage/Editor/AIEngineerControlCenter.cs").read_text(encoding="utf-8")
        self.assertIn('MenuItem("AI Engineer/Control Center")', source)
        self.assertIn("Send to local model", source)
        self.assertIn("PLAN GUARDRAILS", source)
        self.assertIn("review before change", source)
        self.assertIn("AutonomousRequestSender.Plan", source)
        self.assertIn("AIEngineerLocalization", source)
        self.assertIn("EditorGUILayout.Popup", source)
        self.assertIn('"English"', source)
        self.assertIn("Choose Python executable", source)
        self.assertIn("OpenUserGuide", source)
        self.assertIn("SelectedModelMode", source)
        self.assertIn("previousQuickPrompt", source)
        self.assertIn("Approve and apply autonomously", source)
        self.assertIn('"qwen_code"', source)
        self.assertIn('"codex"', source)
        self.assertIn("ProviderSetupManager", source)
        self.assertIn("Yerel (30B / otonom)", source)
        self.assertNotIn('pendingChangeSet != null && SelectedModelMode() != "local"', source)
        self.assertIn("Qwen hesabini bagla", source)
        self.assertIn("Qwen baglantisini kontrol et", source)
        self.assertIn("EnsureTextures", source)
        self.assertNotIn("static readonly Texture2D HeaderTexture", source)
        self.assertIn("workspaceScroll = EditorGUILayout.BeginScrollView", source)
        self.assertIn("responseStyle.CalcHeight", source)
        self.assertIn("EditorApplication.delayCall += () => StartQueuedChangeSet", source)
        self.assertIn("StartQueuedChangeSet", source)

    def test_exporter_includes_every_asset_under_the_package_root(self):
        source = Path("UnityPackage/Editor/AIEngineerPackageExporter.cs").read_text(encoding="utf-8")
        self.assertIn('PackageRoot = "Assets/AIEngineer"', source)
        self.assertIn("AssetDatabase.ExportPackage", source)
        self.assertIn("ExportPackageOptions.Recurse", source)
        self.assertIn("AIEngineer-Complete.unitypackage", source)
        self.assertTrue(Path("UnityPackage/INSTALL.md").is_file())
        self.assertTrue(Path("UnityPackage/BASKA_PC_KURULUM.md").is_file())
        self.assertTrue(Path("UnityPackage/Documentation/AIEngineer-Python-Backend.zip").is_file())
        server = Path("UnityPackage/Editor/ServerManager.cs").read_text(encoding="utf-8")
        self.assertIn("AIEngineer.BackendRoot", server)
        self.assertIn("Python backend not found", server)
        self.assertIn("AIEngineer.PythonExecutable", server)
        self.assertIn("codex-primary-runtime", server)

        localization = Path("UnityPackage/Editor/AIEngineerLocalization.cs").read_text(encoding="utf-8")
        self.assertIn("AIEngineer.Language", localization)
        self.assertIn("AIEngineerLanguage.Turkish", localization)
        self.assertIn("QuickPromptsFor", localization)
        self.assertTrue(Path("UnityPackage/CONTROL_CENTER_KULLANIM_KILAVUZU.md").is_file())
        self.assertTrue(Path("UnityPackage/MODEL_VE_OTONOM_KULLANIM.md").is_file())
        self.assertTrue(Path("UnityPackage/Editor/ProviderSetupManager.cs").is_file())
        self.assertTrue(Path("UnityPackage/Editor/AIEngineerProviderWindow.cs").is_file())
        self.assertTrue(Path("UnityPackage/Editor/LocalModelDownloadMonitor.cs").is_file())
        provider_source = Path("UnityPackage/Editor/ProviderSetupManager.cs").read_text(encoding="utf-8")
        self.assertIn("OpenQwenAccountSignIn", provider_source)
        self.assertIn("QwenModelStudioUrl", provider_source)
        self.assertIn("IsQwenProviderConfigured", provider_source)
        provider_window = Path("UnityPackage/Editor/AIEngineerProviderWindow.cs").read_text(encoding="utf-8")
        self.assertIn("Codex Plus girisini ac", provider_window)
        self.assertIn("AI Engineer/Providers/Hesap Baglantilari", provider_window)
        local_monitor = Path("UnityPackage/Editor/LocalModelDownloadMonitor.cs").read_text(encoding="utf-8")
        self.assertIn("qwen3:30b indiriliyor", local_monitor)
        self.assertIn("fsutil.exe", local_monitor)
        executor = Path("UnityPackage/Editor/AutonomousChangeSetExecutor.cs").read_text(encoding="utf-8")
        planner = Path("Source/Core/Planner/autonomous_change_planner.py").read_text(encoding="utf-8")
        self.assertIn('case "create_ui_screen"', executor)
        self.assertIn("CreateUiScreen", executor)
        self.assertIn("ValidateAppliedOperations", executor)
        self.assertIn("CreateExactReferenceScreen", executor)
        self.assertIn("saveAsScene", executor)
        self.assertIn("NewSceneMode.Additive", executor)
        self.assertIn("StartGameButtonAction", executor)
        self.assertIn("referenceLayout", executor)
        self.assertIn("GetCtaAnchors", executor)
        self.assertIn("ApplyReferenceImage", executor)
        self.assertIn("create_ui_screen", planner)
        self.assertIn("requested_language", planner)
        models = Path("UnityPackage/Editor/AutonomousChangeModels.cs").read_text(encoding="utf-8")
        runner = Path("UnityPackage/Editor/AutonomousJobRunner.cs").read_text(encoding="utf-8")
        self.assertIn("LocalizeGeneratedText", models)
        self.assertIn("LocalizeDiagnostic", runner)
        self.assertIn("ValidateAppliedOperations(state.changeSet)", runner)
        exporter = Path("UnityPackage/Editor/ProjectExporter.cs").read_text(encoding="utf-8")
        scene_model = Path("UnityPackage/Runtime/Scene/ProjectModel.cs").read_text(encoding="utf-8")
        self.assertIn("GetScenes", exporter)
        self.assertIn("public string[] scenes", scene_model)
        start_action = Path("UnityPackage/Runtime/StartGameButtonAction.cs").read_text(encoding="utf-8")
        self.assertIn("currentScenePath", start_action)
        self.assertIn("requestedScenePath", start_action)
        sender = Path("UnityPackage/Editor/AutonomousRequestSender.cs").read_text(encoding="utf-8")
        self.assertIn("PrepareReferenceImage", sender)
        transaction = Path("UnityPackage/Editor/ChangeSetTransaction.cs").read_text(encoding="utf-8")
        self.assertIn("Assets/AIEngineerGenerated/Games/", transaction)
        self.assertIn("Protected sample scene copied to editable game output", transaction)
        self.assertIn("IsProtectedPackagePath", transaction)
        scaffolder = Path("UnityPackage/Editor/Games/GameProjectScaffolder.cs").read_text(encoding="utf-8")
        self.assertIn('OutputRoot = "Assets/AIEngineerGenerated/Games"', scaffolder)
        server = Path("Source/Server/autonomous_server.py").read_text(encoding="utf-8")
        ollama = Path("Source/LLM/ollama_client.py").read_text(encoding="utf-8")
        self.assertIn("ThreadingHTTPServer", server)
        self.assertIn('task == "retrieval"', ollama)
        self.assertIn("6144 if task", ollama)

    def test_backend_html_parser_needs_no_external_beautifulsoup_package(self):
        from Source.Indexer.parser import UnityDocumentParser

        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "page.html"
            page.write_text("<html><title>Unity Test</title><p>This paragraph is long enough to keep.</p><pre>void Awake() {}</pre></html>", encoding="utf-8")
            result = UnityDocumentParser().parse(page)
        self.assertEqual(result["title"], "Unity Test")
        self.assertEqual(len(result["paragraphs"]), 1)
        self.assertIn("Awake", result["code_blocks"][0])

    def test_successful_http_access_logs_are_not_reported_as_backend_errors(self):
        server = Path("Source/Server/autonomous_server.py").read_text(encoding="utf-8")
        manager = Path("UnityPackage/Editor/ServerManager.cs").read_text(encoding="utf-8")
        self.assertIn("def log_message", server)
        self.assertIn('[HTTP]', server)
        self.assertIn('e.Data.Contains(" 200 -")', manager)

    def test_qwen_and_codex_use_account_failover_without_local_mutation_fallback(self):
        router = Path("Source/LLM/llm_client.py").read_text(encoding="utf-8")
        qwen = Path("Source/LLM/qwen_code_client.py").read_text(encoding="utf-8")
        codex = Path("Source/LLM/codex_cli_client.py").read_text(encoding="utf-8")
        self.assertIn("AccountFailoverClient", router)
        self.assertIn("require_account=True", router)
        self.assertNotIn("local-ollama-fallback", router)
        self.assertIn("--exclude-tools", qwen)
        self.assertIn("shell,write,edit", qwen)
        self.assertIn('"--sandbox", "read-only"', codex)
        self.assertIn('"--ask-for-approval", "never"', codex)

    def test_ball_pop_lightning_is_a_real_review_and_apply_feature(self):
        observer = Path("UnityPackage/Runtime/Games/BallPopLightningObserver.cs").read_text(encoding="utf-8")
        installer = Path("UnityPackage/Editor/Games/FeatureApplicationService.cs").read_text(encoding="utf-8")
        acceptance = Path("UnityPackage/Editor/Games/FeatureAcceptanceRunner.cs").read_text(encoding="utf-8")
        self.assertIn("DetectNewHitEffects", observer)
        self.assertIn("StartCoroutine(Strike", observer)
        self.assertIn("Lightning Hit Blue.prefab", installer)
        self.assertIn("InstallBallPopLightning", installer)
        self.assertIn("EditorSceneManager.SaveScene", installer)
        self.assertIn("EnteredPlayMode", acceptance)
        self.assertIn("[AI Acceptance] PASS", acceptance)

    def test_legacy_duplicate_entries_are_hidden_from_ai_engineer_menu(self):
        legacy = "\n".join(
            Path(path).read_text(encoding="utf-8-sig")
            for path in (
                "UnityPackage/Editor/AIWindow.cs",
                "UnityPackage/Editor/AIBridge.cs",
                "UnityPackage/Editor/UnityReflectionScanner.cs",
            )
        )
        self.assertNotIn('MenuItem("AI Engineer/Open AI")', legacy)
        self.assertNotIn('MenuItem("AI Engineer/Open Bridge")', legacy)
        self.assertNotIn('MenuItem("AI Engineer/Export Reflection")', legacy)


if __name__ == "__main__":
    unittest.main()
