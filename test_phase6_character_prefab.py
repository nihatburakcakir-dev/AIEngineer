import unittest
from pathlib import Path

from Source.Core.Character.character_generator import CharacterClassifier, CharacterPrefabGenerator
from Source.Core.Character.character_pipeline import CharacterGenerationPipeline
from Source.Core.Pipeline.command_pipeline import CommandPipeline
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Core.Vision.models import AssetStyle, SceneComposition, VisualAnalysis


def analysis(dimension="3D", objects=None):
    return VisualAnalysis(
        image_path="wolf.png",
        image_size=(512, 512),
        scene=SceneComposition(objects=objects or ["wolf"], confidence=0.9),
        assets=AssetStyle(dimension=dimension, style="fantasy character", asset_types=["wolf"], confidence=0.9),
    )


class CharacterPrefabTests(unittest.TestCase):
    def test_creature_image_selects_3d_capsule_rigidbody_and_animator(self):
        profile = CharacterClassifier().classify(analysis(), "Kırmızı kurt.png")
        plan = CharacterPrefabGenerator().build_plan(profile)

        self.assertEqual(profile.dimension, "3D")
        self.assertEqual(profile.archetype, "creature")
        self.assertEqual(plan.physics.collider, "CapsuleCollider")
        self.assertEqual(plan.physics.rigidbody, "Rigidbody")
        self.assertEqual(plan.animator.states, ["Idle", "Walk", "Run", "Jump"])
        self.assertIn("FreezeRotationX", plan.physics.constraints)
        self.assertTrue(any(op["action"] == "save_prefab" for op in plan.operations))

    def test_2d_character_uses_2d_physics_and_controller_template(self):
        profile = CharacterClassifier().classify(analysis("2D", ["sprite"]), "hero_sprite.png", "Hero")
        plan = CharacterPrefabGenerator().build_plan(profile)
        code = CharacterPrefabGenerator.controller_code(plan)

        self.assertEqual(plan.physics.collider, "CapsuleCollider2D")
        self.assertEqual(plan.physics.rigidbody, "Rigidbody2D")
        self.assertIn("Rigidbody2D", code)
        self.assertIn("linearVelocity", code)

    def test_pipeline_connects_vision_result_to_drag_drop_prefab_plan(self):
        class VisionStub:
            def analyze(self, image_path):
                return analysis()

        plan = CharacterGenerationPipeline(vision_client=VisionStub()).plan_from_image("Red Wolf.png")

        self.assertTrue(plan.prefab_path.endswith("RedWolf/RedWolf.prefab"))
        self.assertTrue(plan.requires_review)
        self.assertTrue(plan.profile.needs_placeholder_mesh)
        self.assertIn("single image", plan.warnings[0])

    def test_character_plan_reaches_command_pipeline_and_action_planner(self):
        class VisionStub:
            def analyze(self, image_path):
                return analysis()

        command = CommandPipeline().process_character_image("bu karakterden prefab oluştur", "Kırmızı kurt.png", VisionStub())
        action_plan = ActionPlanner().build(command)

        self.assertEqual(command.intent, "BUILD_CHARACTER_PREFAB")
        self.assertEqual(command.target, "KirmiziKurt")
        self.assertEqual(action_plan.action, "BUILD_CHARACTER_PREFAB")
        self.assertEqual(action_plan.context["physics"]["collider"], "CapsuleCollider")
        self.assertEqual(action_plan.context["prefab_path"], "Assets/AIEngineerGenerated/Characters/KirmiziKurt/KirmiziKurt.prefab")

    def test_unity_editor_builder_has_prefab_physics_animator_and_controller_support(self):
        builder = Path("UnityPackage/Editor/CharacterPrefabBuilder.cs").read_text(encoding="utf-8")
        runtime = Path("UnityPackage/Runtime/Characters/GeneratedCharacterController3D.cs").read_text(encoding="utf-8")

        self.assertIn("PrefabUtility.SaveAsPrefabAsset", builder)
        self.assertIn("BuildPendingRequest", builder)
        self.assertIn("InitializeOnLoadMethod", builder)
        self.assertIn("CreateConceptArtBillboard", builder)
        self.assertIn("Universal Render Pipeline/Unlit", builder)
        self.assertIn("AssetDatabase.CreateAsset", builder)
        self.assertIn('"_BaseMap"', builder)
        self.assertIn("AIEngineer/CapsulePortrait", builder)
        self.assertIn("mainTextureScale", builder)
        shader = Path("UnityPackage/Runtime/Characters/CapsulePortraitUnlit.shader").read_text(encoding="utf-8")
        self.assertIn("distanceToCapsule", shader)
        self.assertIn("maskUv", shader)
        self.assertIn("Blend SrcAlpha OneMinusSrcAlpha", shader)
        self.assertIn("CapsuleCollider2D", builder)
        self.assertIn("RigidbodyConstraints.FreezeRotationX", builder)
        self.assertIn('"Idle", "Walk", "Run", "Jump"', builder)
        self.assertIn("GeneratedCharacterController3D", runtime)


if __name__ == "__main__":
    unittest.main()
