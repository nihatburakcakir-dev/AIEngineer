import json
import sys
import tempfile
import unittest
from pathlib import Path

from Source.Core.Knowledge.unity_project_context import UnityProjectContext
from Source.Core.Models.change_protocol import ChangeSetParser, ProtocolError
from Source.Core.Planner.autonomous_change_planner import AutonomousChangePlanner
from Source.LLM.codex_cli_client import CodexCliClient, CodexCliUnavailable
from Source.LLM.llm_client import AccountFailoverClient
from Source.LLM.qwen_code_client import QwenCodeClient
from Source.Knowledge.document_knowledge import DocumentKnowledge
from Source.Core.Vision.image_parser import ImageParser


def valid_response():
    return json.dumps({
        "protocol": "ai-engineer.change-set/v1",
        "requestId": "test-job",
        "summary": "Create a tested score component.",
        "risk": "MEDIUM",
        "requiresConfirmation": True,
        "operations": [{
            "id": "op1", "kind": "write_text",
            "path": "Assets/AIEngineerGenerated/ScoreCounter.cs",
            "content": "using UnityEngine; public sealed class ScoreCounter : MonoBehaviour {}",
            "overwrite": False,
        }],
        "validation": {"compile": True, "playMode": False, "checks": ["ScoreCounter compiles"]},
        "explanation": ["Adds a separate component."], "warnings": [],
    })


class FakeConfig:
    project_root = ""
    vision_model = "llava:test"
    vision_endpoint = "http://local"
    qwen_code_model = "qwen3:test"
    codex_model = ""

    def model_for(self, task):
        return "qwen:test"

    def cloud_model_for(self, task):
        return "cloud:test"


class OrchestrationConfig(FakeConfig):
    orchestration_enabled = True


class FakeRouter:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, prompt, task, system, mode):
        self.calls.append({"prompt": prompt, "task": task, "system": system, "mode": mode})
        return self.responses.pop(0)


class FakeContext:
    def build(self, project_root, request, prompt):
        return {"project_root": project_root, "active_scene": "Assets/Scenes/Main.unity", "relevant_scripts": []}

    @staticmethod
    def as_prompt(context):
        return json.dumps(context)


class AutonomousChangeProtocolTests(unittest.TestCase):
    def test_vision_parser_keeps_ui_evidence_when_kind_is_omitted(self):
        response = {
            "ui": [{"label": "MACERAYA BAŞLA"}],
            "scene": {}, "assets": {}, "camera": {}, "lighting": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "test.png"
            image.write_bytes(b"")
            analysis = ImageParser().parse(image, response)
        self.assertEqual(analysis.ui[0].kind, "other")
        self.assertEqual(analysis.ui[0].label, "MACERAYA BAŞLA")

    def test_turkish_document_terms_find_english_unity_manual_without_model_call(self):
        knowledge = DocumentKnowledge.__new__(DocumentKnowledge)
        knowledge.docs_root = Path(".")
        knowledge.parser = None
        knowledge._index = [
            {"name": "UI.Button", "path": Path("UI.Button.html"), "section": "ScriptReference"},
            {"name": "class-CanvasScaler", "path": Path("class-CanvasScaler.html"), "section": "Manual"},
        ]
        results = knowledge.search("Butonu ekranima sigdir", limit=2)
        self.assertTrue(any("Button" in item["name"] for item in results))
        self.assertTrue(any("CanvasScaler" in item["name"] for item in results))

    def test_parser_accepts_bounded_project_relative_change_set(self):
        change_set = ChangeSetParser().parse(valid_response(), model="qwen:test")
        self.assertEqual(change_set.protocol, "ai-engineer.change-set/v1")
        self.assertEqual(change_set.operations[0].payload["path"], "Assets/AIEngineerGenerated/ScoreCounter.cs")
        self.assertEqual(change_set.model, "qwen:test")

    def test_parser_rejects_path_traversal_and_unknown_operations(self):
        unsafe = json.loads(valid_response())
        unsafe["operations"][0]["path"] = "../ProjectSettings/ProjectSettings.asset"
        with self.assertRaises(ProtocolError):
            ChangeSetParser().parse(unsafe)
        unknown = json.loads(valid_response())
        unknown["operations"][0]["kind"] = "run_shell"
        with self.assertRaises(ProtocolError):
            ChangeSetParser().parse(unknown)

    def test_parser_accepts_bounded_generate_image_operation(self):
        response = json.loads(valid_response())
        response["operations"] = [{
            "id": "image", "kind": "generate_image", "prompt": "blue wolf projectile",
            "outputPath": "Assets/AIEngineerGenerated/Textures/Wolf.png",
            "width": 1024, "height": 1024, "transparent": True, "importType": "Sprite",
        }]

        operation = ChangeSetParser().parse(response).operations[0]

        self.assertEqual(operation.payload["outputPath"], "Assets/AIEngineerGenerated/Textures/Wolf.png")
        self.assertEqual(operation.payload["importType"], "Sprite")

    def test_parser_rejects_unsafe_or_invalid_generated_image_settings(self):
        response = json.loads(valid_response())
        response["operations"] = [{
            "id": "image", "kind": "generate_image", "prompt": "blue wolf",
            "outputPath": "Assets/Textures/Wolf.jpg", "width": 32, "height": "1024",
        }]

        with self.assertRaisesRegex(ProtocolError, "outputPath"):
            ChangeSetParser().parse(response)

    def test_legacy_generated_paths_are_routed_outside_the_protected_package(self):
        response = json.loads(valid_response())
        response["operations"][0]["path"] = "Assets/AIEngineer/GeneratedGames/ZumaPrototype/ZumaPrototype.cs"
        change_set = ChangeSetParser().parse(response)
        self.assertEqual(
            change_set.operations[0].payload["path"],
            "Assets/AIEngineerGenerated/Games/ZumaPrototype/ZumaPrototype.cs",
        )

    def test_parser_rejects_raw_unity_prefab_yaml_writes(self):
        prefab = json.loads(valid_response())
        prefab["operations"][0]["path"] = "Assets/UI/StartMenu.prefab"
        prefab["operations"][0]["content"] = "%YAML 1.1\nGameObject:"
        with self.assertRaisesRegex(ProtocolError, "serialized asset YAML"):
            ChangeSetParser().parse(prefab)

    def test_ui_scene_target_is_mapped_to_runtime_scene_path_and_child_mutation_is_rejected(self):
        response = json.loads(valid_response())
        response["operations"] = [{
            "id": "ui", "kind": "create_ui_screen", "name": "StartScreen", "title": "Start",
            "gameplayTarget": "Assets/Scenes/Gameplay.unity",
        }]
        change_set = ChangeSetParser().parse(response)
        self.assertEqual(change_set.operations[0].payload["gameplayTarget"], "")
        self.assertEqual(change_set.operations[0].payload["gameplayScenePath"], "Assets/Scenes/Gameplay.unity")
        response["operations"].append({
            "id": "button", "kind": "add_component", "targetPath": "StartScreen/Primary Action - START", "component": "Button",
        })
        with self.assertRaisesRegex(ProtocolError, "newly created UI"):
            ChangeSetParser().parse(response)

    def test_ui_asset_path_with_scene_extension_is_mapped_to_scene_path(self):
        response = json.loads(valid_response())
        response["operations"] = [{
            "id": "ui", "kind": "create_ui_screen", "name": "StartScreen", "title": "Start",
            "assetPath": "Assets/UI/StartScreen.unity",
        }]
        change_set = ChangeSetParser().parse(response)
        self.assertEqual(change_set.operations[0].payload["assetPath"], "")
        self.assertEqual(change_set.operations[0].payload["scenePath"], "Assets/UI/StartScreen.unity")

    def test_ui_layout_choices_are_reviewable_model_parameters(self):
        response = json.loads(valid_response())
        response["operations"] = [{
            "id": "ui", "kind": "create_ui_screen", "name": "StartScreen", "title": "Start",
            "referenceLayout": "background", "imageFit": "cover", "ctaAnchor": "bottom_center",
        }]
        change_set = ChangeSetParser().parse(response)
        payload = change_set.operations[0].payload
        self.assertEqual(payload["referenceLayout"], "background")
        self.assertEqual(payload["imageFit"], "cover")
        self.assertEqual(payload["ctaAnchor"], "bottom_center")

    def test_parser_rejects_component_targets_that_are_asset_files(self):
        response = json.loads(valid_response())
        response["operations"] = [{
            "id": "component", "kind": "add_component",
            "targetPath": "Assets/Scenes/Gameplay.unity", "component": "Camera",
        }]
        with self.assertRaisesRegex(ProtocolError, "scene GameObject path"):
            ChangeSetParser().parse(response)

    def test_parser_rejects_component_targets_that_are_csharp_files(self):
        response = json.loads(valid_response())
        response["operations"] = [{
            "id": "component", "kind": "add_component",
            "targetPath": "Assets/Scripts/BallChainManager.cs", "component": "BombBall",
        }]
        with self.assertRaisesRegex(ProtocolError, "scene GameObject path"):
            ChangeSetParser().parse(response)

    def test_grounding_rejects_invented_project_api_and_missing_asset(self):
        response = json.loads(valid_response())
        response["operations"] = [{
            "id": "code", "kind": "write_text", "path": "Assets/AIEngineerGenerated/Scripts/Bomb.cs",
            "content": "class Bomb { void X(){ BallChainManager.Instance.RemoveBall(); } }",
        }]
        change_set = ChangeSetParser().parse(response)
        context = {"script_api": [{"class": "BallChainManager", "public_methods": ["AddBall"]}], "scene_objects": [], "assets": {}}
        with self.assertRaisesRegex(ProtocolError, "missing project API"):
            AutonomousChangePlanner._validate_project_grounding(change_set, context)

    def test_ui_plan_omits_impossible_component_operation_targeting_scene_asset(self):
        response = json.loads(valid_response())
        response["operations"] = [
            {"id": "ui", "kind": "create_ui_screen", "name": "StartScreen", "title": "Start"},
            {"id": "bad", "kind": "add_component", "targetPath": "Assets/Scenes/MainMenu.unity", "component": "Button"},
        ]
        change_set = ChangeSetParser().parse(response)
        self.assertEqual([operation.kind for operation in change_set.operations], ["create_ui_screen"])
        self.assertTrue(any("UI operation was simplified" in warning for warning in change_set.warnings))

    def test_ui_plan_merges_related_prefab_scene_and_material_operations(self):
        response = json.loads(valid_response())
        response["operations"] = [
            {"id": "ui", "kind": "create_ui_screen", "name": "GokKutAtesYolu", "title": "Gök Kurt"},
            {"id": "prefab", "kind": "create_prefab", "name": "GokKutAtesYolu", "assetPath": "Assets/UI/GokKutAtesYolu.prefab"},
            {"id": "scene", "kind": "create_scene", "path": "Assets/UI/GokKutAtesYolu.unity"},
            {"id": "material", "kind": "create_material", "name": "GokKutAtesYolu", "assetPath": "Assets/UI/GokKutAtesYolu.mat"},
        ]
        change_set = ChangeSetParser().parse(response)
        self.assertEqual([operation.kind for operation in change_set.operations], ["create_ui_screen"])
        self.assertEqual(change_set.operations[0].payload["assetPath"], "Assets/UI/GokKutAtesYolu.prefab")
        self.assertTrue(any("UI operation was simplified" in warning for warning in change_set.warnings))

    def test_repair_salvage_still_enforces_original_scope(self):
        previous = json.loads(valid_response())
        previous["operations"].append({"id": "scene", "kind": "create_scene", "path": "Assets/AIEngineerGenerated/Main.unity"})
        truncated_drift = (
            '{"responseType":"change_set","summary":"Drift","risk":"LOW","requiresConfirmation":true,'
            '"operations":[{"id":"replacement","kind":"create_game_object","name":"Wrong"}],'
            '"validation":{"compile":false,"playMode":false,"checks":[]},"explanation":["cut'
        )
        router = FakeRouter([truncated_drift, json.dumps(previous)])
        planner = AutonomousChangePlanner(config=FakeConfig(), router=router, context_builder=FakeContext(), retries=1)
        result = planner.repair({
            "prompt": "Repair the scene", "projectPath": "C:/Unity", "modelMode": "local",
            "changeSet": previous, "diagnostics": ["scene error"],
        })
        self.assertEqual(result.operations[-1].kind, "create_scene")
        self.assertEqual(len(router.calls), 2)

    def test_destructive_or_overwrite_operations_are_elevated_to_high_risk(self):
        overwrite = json.loads(valid_response())
        overwrite["risk"] = "LOW"
        overwrite["operations"][0]["overwrite"] = True
        self.assertEqual(ChangeSetParser().parse(overwrite).risk, "HIGH")

    def test_parser_accepts_mobile_game_entrance_ui_prefab(self):
        response = json.loads(valid_response())
        response["operations"] = [{
            "id": "start-ui", "kind": "create_ui_screen", "name": "Mythic Start UI",
            "title": "Kurtların Yolu", "subtitle": "Mavi ateşi topla ve ormanı koru.",
            "buttonLabel": "MACERAYA BAŞLA", "color": "#48D7C4",
            "assetPath": "Assets/AIEngineerGenerated/UI/MythicStartUI.prefab",
        }]
        change_set = ChangeSetParser().parse(response)
        self.assertEqual(change_set.operations[0].kind, "create_ui_screen")
        self.assertEqual(change_set.operations[0].payload["assetPath"], "Assets/AIEngineerGenerated/UI/MythicStartUI.prefab")

    def test_planner_repairs_invalid_model_json_before_returning(self):
        router = FakeRouter(["not json", valid_response()])
        planner = AutonomousChangePlanner(config=FakeConfig(), router=router, context_builder=FakeContext(), retries=1)
        result = planner.plan({"prompt": "Add a score counter", "projectPath": "C:/Unity", "modelMode": "local"})
        self.assertEqual(result.operations[0].kind, "write_text")
        self.assertEqual(len(router.calls), 2)
        self.assertIn("failed protocol/project validation", router.calls[1]["prompt"])

    def test_local_orchestrator_hands_one_request_from_planner_to_code_specialist(self):
        brief = json.dumps({"behavior": ["Create a wolf prefab"], "distribution": ["Flux image asset", "Qwen Coder Unity wiring"], "feedback": [], "integration": [], "acceptance": []})
        router = FakeRouter([brief, valid_response()])
        planner = AutonomousChangePlanner(config=OrchestrationConfig(), router=router, context_builder=FakeContext())
        result = planner.plan({"prompt": "Create a wolf prefab with a yellow visual", "projectPath": "C:/Unity", "modelMode": "local"})
        self.assertEqual(result.operations[0].kind, "write_text")
        self.assertEqual([call["task"] for call in router.calls], ["feature_analysis", "code_generation"])
        self.assertIn("Flux image asset", router.calls[1]["prompt"])

    def test_default_planner_allows_two_grounding_retries_for_feature_code(self):
        planner = AutonomousChangePlanner(config=FakeConfig(), router=FakeRouter([valid_response()]), context_builder=FakeContext())
        self.assertEqual(planner.retries, 2)

    def test_entrance_ui_request_is_interpreted_by_the_local_model_not_a_keyword_script(self):
        router = FakeRouter([valid_response()])
        planner = AutonomousChangePlanner(config=FakeConfig(), router=router, context_builder=FakeContext())
        result = planner.plan({
            "prompt": "Oyunun temasini ve amacini anlatan mobil giris UI prefab'i olustur",
            "projectPath": "C:/Unity", "activeScene": "Assets/Scenes/WolfPath.unity", "modelMode": "local",
        })
        self.assertEqual(result.operations[0].kind, "write_text")
        self.assertEqual(len(router.calls), 1)

    def test_reference_image_request_instructs_the_local_model_to_make_an_editable_scene_aware_ui(self):
        router = FakeRouter([valid_response()])
        planner = AutonomousChangePlanner(config=FakeConfig(), router=router, context_builder=FakeContext())
        result = planner.plan({
            "prompt": "Referans görselin aynısını istiyorum",
            "projectPath": "C:/Unity", "imagePath": "", "targetOrientation": "landscape", "modelMode": "local",
        })
        self.assertEqual(result.operations[0].kind, "write_text")
        self.assertEqual(len(router.calls), 1)

    def test_context_includes_selected_real_script_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Assets/Scripts").mkdir(parents=True)
            (root / "ProjectSettings").mkdir()
            (root / "ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 6000.3.18f1", encoding="utf-8")
            script = root / "Assets/Scripts/Inventory.cs"
            script.write_text("public sealed class Inventory {}", encoding="utf-8")
            documentation = root / "Assets/Documentation/ParticleEffects.md"
            documentation.parent.mkdir(parents=True)
            documentation.write_text("ParticleSystem supports startLifetime and startColor.", encoding="utf-8")
            context = UnityProjectContext().build(root, {
                "selectedAssets": ["Assets/Scripts/Inventory.cs"],
                "project": {"scenes": ["Assets/Scenes/Gameplay.unity"]},
            }, "envanteri düzelt")
        self.assertEqual(context["unity_version"], "6000.3.18f1")
        self.assertEqual(context["relevant_scripts"][0]["path"], "Assets/Scripts/Inventory.cs")
        self.assertIn("sealed class Inventory", context["relevant_scripts"][0]["content"])
        self.assertTrue(context["unity_documentation"])
        self.assertIn("ParticleSystem", context["unity_documentation"][0]["content"])
        self.assertEqual(context["assets"]["scenes"], ["Assets/Scenes/Gameplay.unity"])

    def test_repair_cannot_escape_original_files_or_drop_scene_behavior(self):
        previous = json.loads(valid_response())
        previous["operations"].append({"id": "op2", "kind": "create_game_object", "name": "Score Host", "primitive": "Cube"})
        escaped = json.loads(valid_response())
        escaped["operations"][0]["path"] = "Assets/Scripts/Unrelated.cs"
        repaired = json.loads(valid_response())
        repaired["operations"][0]["overwrite"] = True
        repaired["operations"].append({"id": "op2", "kind": "create_game_object", "name": "Score Host", "primitive": "Cube"})
        router = FakeRouter([json.dumps(escaped), json.dumps(repaired)])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "Assets/AIEngineerGenerated/ScoreCounter.cs"
            target.parent.mkdir(parents=True)
            target.write_text("broken", encoding="utf-8")
            planner = AutonomousChangePlanner(config=FakeConfig(), router=router, context_builder=FakeContext(), retries=1)
            result = planner.repair({
                "prompt": "Fix score counter", "projectPath": str(root), "modelMode": "local",
                "changeSet": previous, "diagnostics": ["ScoreCounter.cs(1): ; expected"],
            })
        self.assertEqual(result.operations[0].payload["path"], "Assets/AIEngineerGenerated/ScoreCounter.cs")
        self.assertEqual(len(router.calls), 2)
        self.assertIn("escaped original path scope", router.calls[1]["prompt"])

    def test_common_semicolon_error_is_repaired_without_model_drift(self):
        previous = json.loads(valid_response())
        previous["operations"][0]["path"] = "Assets/AIEngineerGenerated/AutoRepairProbe.cs"
        previous["operations"][0]["content"] = "using UnityEngine;\npublic class AutoRepairProbe : MonoBehaviour\n{\n    void Update()\n    {\n        transform.Rotate(Vector3.up)\n    }\n}\n"
        router = FakeRouter([])
        planner = AutonomousChangePlanner(config=FakeConfig(), router=router, context_builder=FakeContext())
        result = planner.repair({
            "prompt": "Fix AutoRepairProbe", "projectPath": "C:/Unity", "modelMode": "local",
            "changeSet": previous,
            "diagnostics": [r"Assets\AIEngineerGenerated\AutoRepairProbe.cs(6,37): error CS1002: ; expected"],
        })
        self.assertIn("transform.Rotate(Vector3.up);", result.operations[0].payload["content"])
        self.assertEqual(result.model, "compiler-rule-engine")
        self.assertEqual(router.calls, [])

    def test_qwen_code_is_read_only_agent_and_returns_manifest_text(self):
        captured = {}

        def runner(args, input_text, cwd, timeout, environment):
            captured.update(args=args, input=input_text, cwd=cwd, timeout=timeout, environment=environment)
            return 0, json.dumps([
                {"type": "system", "subtype": "session_start"},
                {"type": "result", "subtype": "success", "result": valid_response()},
            ]), ""

        client = QwenCodeClient(
            executable=sys.executable, model="qwen3:test", base_url="http://127.0.0.1:11434/v1",
            working_directory=".", prefer_account=False, runner=runner,
        )
        self.assertEqual(json.loads(client.generate("Create score", system="JSON only"))["protocol"], "ai-engineer.change-set/v1")
        self.assertIn("--safe-mode", captured["args"])
        self.assertIn("shell,write,edit,agent,web_fetch,web_search", captured["args"])
        self.assertEqual(captured["args"][captured["args"].index("--max-tool-calls") + 1], "25")
        self.assertEqual(captured["environment"]["OPENAI_BASE_URL"], "http://127.0.0.1:11434/v1")
        self.assertEqual(captured["environment"]["OPENAI_API_KEY"], "ollama")

    def test_codex_plus_provider_can_inspect_but_cannot_write_directly(self):
        captured = {}

        def runner(args, input_text, cwd, timeout, environment):
            captured.update(args=args, input=input_text, cwd=cwd, timeout=timeout)
            return 0, valid_response(), ""

        client = CodexCliClient(executable=sys.executable, working_directory=".", network_checker=lambda: True, runner=runner)
        self.assertEqual(json.loads(client.generate("Create score", system="JSON only"))["protocol"], "ai-engineer.change-set/v1")
        self.assertIn("exec", captured["args"])
        self.assertEqual(captured["args"][captured["args"].index("--sandbox") + 1], "read-only")
        self.assertEqual(captured["args"][captured["args"].index("--ask-for-approval") + 1], "never")
        self.assertIn("do not edit files", captured["args"][-1])

    def test_planner_accepts_qwen_code_and_codex_modes(self):
        for mode, expected_model in (("qwen_code", "qwen-code/qwen3:test"), ("codex", "codex-cli/chatgpt-default")):
            router = FakeRouter([valid_response()])
            planner = AutonomousChangePlanner(config=FakeConfig(), router=router, context_builder=FakeContext())
            result = planner.plan({"prompt": "Add a score counter", "projectPath": "C:/Unity", "modelMode": mode})
            self.assertEqual(result.model, expected_model)
            self.assertEqual(router.calls[0]["mode"], mode)

    def test_account_provider_failure_tries_the_other_account_not_local_model(self):
        class UnavailableQwen:
            @staticmethod
            def generate(prompt, task="chat", system=""):
                raise CodexCliUnavailable("offline")

        class CodexAccount:
            @staticmethod
            def generate(prompt, task="chat", system=""):
                return valid_response()

        client = AccountFailoverClient(UnavailableQwen(), CodexAccount())
        self.assertEqual(json.loads(client.generate("Create score"))["protocol"], "ai-engineer.change-set/v1")
        self.assertEqual(client.last_provider, "CodexAccount")

    def test_local_plans_have_a_bounded_generation_budget(self):
        captured = {}

        def transport(endpoint, payload):
            captured.update(payload)
            return {"message": {"content": valid_response()}}

        from Source.LLM.ollama_client import OllamaClient
        OllamaClient(model="qwen3:test", transport=transport).generate("Create UI", task="code_generation")
        self.assertEqual(captured["options"]["num_predict"], 6144)
        self.assertIsInstance(captured["format"], dict)
        self.assertIn("change_set", captured["format"]["properties"]["responseType"]["enum"])
        self.assertNotIn("role", captured["format"]["properties"])
        operation_variants = captured["format"]["properties"]["operations"]["items"]["oneOf"]
        add_component = next(item for item in operation_variants if item["properties"]["kind"]["enum"] == ["add_component"])
        self.assertIn("targetPath", add_component["required"])
        self.assertIn("component", add_component["required"])

    def test_normal_answer_uses_one_model_call_without_a_second_review(self):
        response = json.dumps({
            "protocol": "ai-engineer.change-set/v1", "responseType": "answer",
            "answer": "Canvas Scaler arayuzu hedef cozunurluge uyarlar.", "operations": [],
            "risk": "LOW", "requiresConfirmation": False,
            "validation": {"compile": False, "playMode": False, "checks": []},
        })
        router = FakeRouter([response])
        planner = AutonomousChangePlanner(config=FakeConfig(), router=router, context_builder=FakeContext())
        result = planner.plan({"prompt": "Canvas Scaler nedir?", "projectPath": "C:/Unity", "modelMode": "local"})
        self.assertEqual(result.responseType, "answer")
        self.assertEqual(len(router.calls), 1)

    def test_parser_accepts_grounded_answer_without_fake_operations(self):
        response = {
            "protocol": "ai-engineer.change-set/v1", "responseType": "answer",
            "answer": "Canvas Scaler ekran boyutuna göre UI ölçekler.", "operations": [],
            "risk": "LOW", "requiresConfirmation": False,
            "validation": {"compile": False, "playMode": False, "checks": []},
        }
        result = ChangeSetParser().parse(response, model="qwen3:test")
        self.assertEqual(result.responseType, "answer")
        self.assertEqual(result.operations, [])

    def test_parser_salvages_complete_answer_but_never_partial_actions(self):
        parser = ChangeSetParser()
        truncated_answer = '{"protocol":"ai-engineer.change-set/v1","responseType":"answer","answer":"Tam cevap metni","operations":'
        recovered = parser.salvage_complete_answer(truncated_answer, model="qwen3:test")
        self.assertEqual(recovered.answer, "Tam cevap metni")
        self.assertIsNone(parser.salvage_complete_answer('{"responseType":"change_set","operations":[{', model="qwen3:test"))

    def test_parser_salvages_only_a_fully_closed_operation_array(self):
        parser = ChangeSetParser()
        response = '{"responseType":"change_set","summary":"Create probe","risk":"LOW","requiresConfirmation":true,"operations":[{"id":"op1","kind":"create_game_object","name":"Probe"}],"validation":{"compile":false,"playMode":false,"checks":[]},"explanation":["truncated'
        recovered = parser.salvage_complete_change_set(response, model="qwen3:test")
        self.assertEqual(recovered.operations[0].kind, "create_game_object")
        self.assertIsNone(parser.salvage_complete_change_set('{"responseType":"change_set","summary":"x","operations":[{"kind":"create_game_object"', model="qwen3:test"))


if __name__ == "__main__":
    unittest.main()
