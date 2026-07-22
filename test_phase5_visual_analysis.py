import tempfile
import unittest
from pathlib import Path

from Source.Core.Fusion.visual_fusion import VisualFusionEngine
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Core.Pipeline.command_pipeline import CommandPipeline
from Source.Core.Vision.image_parser import ImageParseError, ImageParser
from Source.Core.Vision.unity_visual_mapper import UnityVisualMapper
from Source.Core.Vision.vision_client import VisionClient


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0dIDATx\x9cc\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
)


def visual_response():
    return {
        "ui": [
            {"kind": "panel", "label": "Inventory", "layout": "top-right", "confidence": 0.95},
            {"kind": "grid", "label": "Slots", "layout": "grid", "confidence": 0.90},
        ],
        "scene": {"objects": ["hero", "ground", "trees"], "composition": "hero centered", "depth": "layered", "confidence": 0.88},
        "assets": {"dimension": "3D", "style": "stylized", "asset_types": ["character", "environment"], "confidence": 0.86},
        "camera": {"angle": "top-down", "projection": "orthographic", "framing": "wide", "confidence": 0.93},
        "lighting": {"direction": "top-left", "color": "warm", "atmosphere": "bright", "confidence": 0.80},
    }


class VisualAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.image = Path(self.temp_dir.name) / "reference.png"
        self.image.write_bytes(PNG_1X1)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_local_vision_client_parses_all_five_dimensions(self):
        received = {}

        def transport(payload):
            received.update(payload)
            return {"message": {"content": visual_response()}}

        analysis = VisionClient(model="local-vision", transport=transport).analyze(self.image)

        self.assertEqual(analysis.image_size, (1, 1))
        self.assertEqual(analysis.camera.angle, "top-down")
        self.assertEqual(analysis.assets.dimension, "3D")
        self.assertEqual(analysis.ui[1].kind, "grid")
        self.assertEqual(analysis.lighting.atmosphere, "bright")
        self.assertEqual(received["model"], "local-vision")
        self.assertTrue(received["messages"][0]["images"][0])

    def test_parser_rejects_partial_or_unstructured_perception(self):
        with self.assertRaises(ImageParseError):
            ImageParser().parse(self.image, {"ui": []})

    def test_vision_client_retries_an_incomplete_local_model_response(self):
        responses = [{"ui": []}, visual_response()]
        client = VisionClient(transport=lambda _: responses.pop(0), retries=1)

        analysis = client.analyze(self.image)

        self.assertEqual(analysis.camera.angle, "top-down")
        self.assertEqual(responses, [])

    def test_vision_client_keeps_valid_initial_evidence_when_repair_is_unfinished(self):
        partial = visual_response()
        partial["camera"]["angle"] = "unknown"
        responses = [partial, {"done": False}]
        analysis = VisionClient(transport=lambda _: responses.pop(0), retries=1).analyze(self.image)
        self.assertEqual(analysis.assets.dimension, "3D")
        self.assertEqual(analysis.camera.angle, "unknown")

    def test_parser_normalizes_common_local_model_aliases(self):
        response = {
            "ui": ["Race Track"],
            "scene": {"objects": ["track"]},
            "assets": {"models": ["track"], "textures": ["stone"]},
            "camera": {"angle": "top-down", "projection": "perspective"},
            "lighting": {"ambient": {"color": "warm"}},
        }

        analysis = ImageParser().parse(self.image, response)

        self.assertEqual(analysis.ui[0].label, "Race Track")
        self.assertEqual(analysis.assets.dimension, "3D")
        self.assertEqual(analysis.assets.asset_types, ["track", "stone"])
        self.assertEqual(analysis.lighting.atmosphere, "ambient lighting")

    def test_parser_normalizes_dimension_enum_and_mapper_ignores_scene_object_as_ui(self):
        response = visual_response()
        response["assets"]["dimension"] = "2D|3D|mixed"
        response["ui"] = [{"kind": "Road", "label": "road", "confidence": 0.9}]
        analysis = ImageParser().parse(self.image, response)
        plan = UnityVisualMapper().map(analysis)

        self.assertEqual(analysis.assets.dimension, "mixed")
        self.assertTrue(any(command["action"] == "set_art_direction" for command in plan.commands))
        self.assertFalse(any(command["action"] == "create_canvas" for command in plan.commands))

    def test_visual_mapper_selects_camera_canvas_and_grid_layout(self):
        analysis = VisionClient(transport=lambda _: visual_response()).analyze(self.image)
        plan = UnityVisualMapper().map(analysis)

        self.assertIn({"action": "create_canvas", "render_mode": "ScreenSpaceOverlay", "risk": "LOW"}, plan.commands)
        self.assertTrue(any(command["action"] == "create_ui_grid" and command["component"] == "GridLayoutGroup" for command in plan.commands))
        camera = next(command for command in plan.commands if command["action"] == "create_camera")
        self.assertEqual(camera["projection"], "Orthographic")
        self.assertEqual(camera["suggested_package"], "com.unity.cinemachine")

    def test_visual_plan_reaches_command_pipeline_and_action_planner(self):
        client = VisionClient(transport=lambda _: visual_response())
        command = CommandPipeline().process_image("bu görseldeki UI'yi kur", str(self.image), client)
        action_plan = ActionPlanner().build(command)

        self.assertEqual(command.intent, "BUILD_FROM_IMAGE")
        self.assertEqual(action_plan.action, "BUILD_FROM_IMAGE")
        self.assertEqual(action_plan.context["visual_analysis"]["camera"]["angle"], "top-down")
        self.assertEqual(action_plan.context["unity_context"]["render_pipeline"], "URP")
        self.assertTrue(any(step["action"] == "create_ui_grid" for step in action_plan.steps))

    def test_fusion_engine_keeps_uncertain_camera_reviewable(self):
        result = visual_response()
        result["camera"] = {"angle": "unknown", "projection": "unknown", "framing": "", "confidence": 0.1}
        analysis, plan = VisualFusionEngine(vision_client=VisionClient(transport=lambda _: result)).analyze_and_plan(self.image)

        self.assertEqual(analysis.camera.angle, "unknown")
        self.assertTrue(plan.warnings)
        self.assertFalse(any(command["action"] == "create_camera" for command in plan.commands))


if __name__ == "__main__":
    unittest.main()
