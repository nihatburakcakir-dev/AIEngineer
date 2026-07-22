import tempfile
import unittest
from pathlib import Path

from Source.Core.Executor.autonomous_executor import AutonomousExecutor, ExecutionStep, PerceptionResult
from Source.Core.Game.end_to_end_game_pipeline import EndToEndGamePipeline, ReferencePrototypeEvaluation
from Source.Core.Models.command import AICommand
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Core.Vision.models import AssetStyle, CameraAnalysis, LightingAnalysis, SceneComposition, VisualAnalysis
from Source.Core.Vision.unity_visual_mapper import UnityVisualMapper


class StubVisionClient:
    def analyze(self, image_path):
        return VisualAnalysis(
            str(image_path), (1536, 1024), [],
            SceneComposition(["winding stone path", "cave entrance", "crystals"], "top-down game board", "layered"),
            AssetStyle("2D", "painted fantasy", ["environment", "path"], 0.9),
            CameraAnalysis("top-down", "orthographic", "whole board", 0.9),
            LightingAnalysis("torches", "warm and blue", "fantasy cave", 0.9),
            "stub-vision",
        )


class EndToEndGameTests(unittest.TestCase):
    def test_one_command_preserves_visual_evidence_and_creates_a_zuma_request(self):
        command = AICommand(prompt="Bu ekran görüntüsündeki Zuma tarzı oyunu oluştur")
        result = EndToEndGamePipeline(vision_client=StubVisionClient()).attach(command, "reference.png", "Reference Zuma Prototype")
        self.assertEqual(result.intent, "BUILD_GAME_FROM_REFERENCE")
        self.assertEqual(result.target, "ReferenceZumaPrototype")
        self.assertEqual(result.metadata["game_build_request"]["gameKey"], "zuma_match")
        self.assertEqual(result.metadata["end_to_end_game_plan"]["phase_chain"], ["phase5_visual_analysis", "phase7_game_generation", "phase2_autonomous_validation"])
        self.assertEqual(result.metadata["visual_analysis"]["camera"]["angle"], "top-down")

    def test_action_plan_requires_visual_game_and_autonomous_validation_stages(self):
        command = AICommand(prompt="Bu ekran görüntüsündeki Zuma tarzı oyunu oluştur")
        command = EndToEndGamePipeline(vision_client=StubVisionClient()).attach(command, "reference.png", "Reference Zuma Prototype")
        plan = ActionPlanner().build(command)
        self.assertEqual(plan.action, "BUILD_GAME_FROM_REFERENCE")
        self.assertEqual(plan.context["phase_chain"][-1], "phase2_autonomous_validation")
        self.assertIn("compile_playmode_validation", plan.steps[-1])

    def test_validator_requires_scene_compile_playmode_and_gameplay_signals(self):
        expected_scene = "Assets/AIEngineerGenerated/Games/ReferenceZumaPrototype/ReferenceZumaPrototype.unity"
        signals = ["chain_spawns", "projectile_fires"]
        failed = ReferencePrototypeEvaluation.from_unity_result({"compiled": True, "play_mode_verified": False, "scene_path": expected_scene, "acceptance_signals": signals}, expected_scene, signals)
        passed = ReferencePrototypeEvaluation.from_unity_result({"compiled": True, "play_mode_verified": True, "scene_path": expected_scene, "acceptance_signals": signals}, expected_scene, signals)
        self.assertFalse(failed.valid)
        self.assertIn("play_mode_verified", failed.missing)
        self.assertTrue(passed.valid)

    def test_visual_mapper_normalizes_local_model_camera_phrasing(self):
        analysis = StubVisionClient().analyze("reference.png")
        analysis.camera.angle = "Top-down view of the board"
        analysis.camera.projection = "Orthographic projection"
        plan = UnityVisualMapper().map(analysis)
        self.assertEqual(plan.commands[0]["action"], "create_camera")
        self.assertEqual(plan.commands[0]["angle"], "top-down")

    def test_phase2_repair_loop_can_recover_a_failed_reference_prototype_validation(self):
        state = {"valid": False}
        executor = AutonomousExecutor([lambda: PerceptionResult(state["valid"], "playmode failed" if not state["valid"] else "playmode passed")], max_attempts=2)
        result = executor.run(
            [ExecutionStep("CREATE_OBJECT", lambda: True)],
            repair_planner=lambda perception, attempt: [ExecutionStep("CREATE_OBJECT", lambda: state.update(valid=True) is None)],
        )
        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 2)

    def test_reference_prototype_builder_has_mobile_safe_turkish_mythology_presentation(self):
        builder = Path("UnityPackage/Editor/Games/GameProjectScaffolder.cs").read_text(encoding="utf-8")
        self.assertIn("referenceResolution = new Vector2(1080f, 1920f)", builder)
        self.assertIn("Bozkurt Gate", builder)
        self.assertIn("Ergenekon Forge", builder)
        self.assertIn("ATES ET", builder)


if __name__ == "__main__":
    unittest.main()
