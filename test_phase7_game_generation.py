import json
import tempfile
import unittest
from pathlib import Path

from Source.Core.Game.game_pipeline import GameGenerationPipeline
from Source.Core.Game.project_scaffolder import ProjectScaffolder
from Source.Core.Game.reference_game_input import ReferenceGameLibrary
from Source.Core.Pipeline.command_pipeline import CommandPipeline
from Source.Core.Planner.action_planner import ActionPlanner


class GameGenerationTests(unittest.TestCase):
    def test_library_covers_five_known_game_types(self):
        library = ReferenceGameLibrary()
        self.assertGreaterEqual(len(library.templates), 25)
        self.assertEqual(library.resolve("Zuma tarzı oyun oluştur").key, "zuma_match")
        self.assertEqual(library.resolve("top down survival yap").key, "top_down_survival")
        self.assertEqual(library.resolve("FPS oyunu yap").key, "first_person_shooter")
        self.assertEqual(library.resolve("Subway Surfers gibi koşu oyunu").key, "subway_endless_runner")
        self.assertEqual(library.resolve("LOL gibi MOBA yap").key, "moba_lane_arena")
        self.assertEqual(library.resolve("kule savunma oyunu yap").key, "tower_defense")
        self.assertEqual(library.resolve("turn based strategy game").key, "turn_based_strategy")
        self.assertEqual(library.resolve("ritim oyunu yap").key, "rhythm_game")

    def test_zuma_plan_contains_the_required_systems_and_stages(self):
        plan = GameGenerationPipeline().plan("Zuma tarzı basit bir oyun oluştur")
        self.assertEqual(plan.game_name, "ZumaMatch")
        self.assertIn("marble_chain", plan.systems)
        self.assertIn("match_resolution", plan.systems)
        self.assertEqual(plan.progress_stages[-1], "play_mode_verified")
        self.assertTrue(plan.scene_path.endswith("ZumaMatch/ZumaMatch.unity"))

    def test_request_is_serializable_for_the_unity_editor_builder(self):
        plan = GameGenerationPipeline().plan("zuma oyunu oluştur")
        with tempfile.TemporaryDirectory() as directory:
            output = ProjectScaffolder().write_request(plan, Path(directory) / "GameBuildRequest.json")
            request = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(request["gameKey"], "zuma_match")
        self.assertTrue(request["autoPlayValidation"])
        self.assertIn("score_increases", request["acceptanceSignals"])

    def test_game_request_reaches_action_planner_as_a_staged_high_risk_plan(self):
        command = CommandPipeline().process_game_request("Zuma tarzı oyun oluştur")
        action_plan = ActionPlanner().build(command)
        self.assertEqual(command.intent, "BUILD_GAME_PROTOTYPE")
        self.assertEqual(action_plan.action, "BUILD_GAME_PROTOTYPE")
        self.assertEqual(action_plan.risk, "HIGH")
        self.assertIn("play_mode_verified", action_plan.steps)

    def test_unity_builder_and_runtime_have_zuma_mechanics_and_play_validation(self):
        builder = Path("UnityPackage/Editor/Games/GameProjectScaffolder.cs").read_text(encoding="utf-8")
        runtime = Path("UnityPackage/Runtime/Games/ZumaGameManager.cs").read_text(encoding="utf-8")
        shooter = Path("UnityPackage/Runtime/Games/ZumaShooter.cs").read_text(encoding="utf-8")
        self.assertIn("BuildPendingRequest", builder)
        self.assertIn("EditorSceneManager.SaveScene", builder)
        self.assertIn("ZumaPrototype", builder)
        self.assertIn("ZumaPlayModeValidator", builder)
        self.assertIn("ResolveHit", runtime)
        self.assertIn("Score", runtime)
        self.assertIn("MechanicsVerified", runtime)
        marble = Path("UnityPackage/Runtime/Games/ZumaMarble.cs").read_text(encoding="utf-8")
        self.assertIn("Register(this)", marble)
        self.assertIn("[SerializeField] private Color marbleColor", marble)
        self.assertIn("Fire", shooter)
        self.assertIn("Input.touchCount", shooter)
        self.assertIn("FireForward", shooter)
        self.assertIn("IsPointerOverGameObject", shooter)
        self.assertIn("CanvasScaler", builder)
        self.assertIn("ScaleWithScreenSize", builder)
        self.assertIn("GOKBORU: ATES YOLU", builder)
        self.assertIn("CreateWindingMarblePath", builder)
        self.assertIn("TurkishMythologyEnvironment", builder)


if __name__ == "__main__":
    unittest.main()
