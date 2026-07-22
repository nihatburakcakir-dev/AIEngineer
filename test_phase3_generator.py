import tempfile
import unittest
import json
from pathlib import Path

from Source.Core.Generator.code_generator import CodeGenerator
from Source.Knowledge.unity_expertise import UnityExpertise


class UnityGeneratorTests(unittest.TestCase):
    def test_addressables_template_has_safe_release_and_pipeline_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "ProjectSettings").mkdir()
            (project / "Packages").mkdir()
            (project / "ProjectSettings" / "GraphicsSettings.asset").write_text(
                "UniversalRenderPipeline", encoding="utf-8"
            )
            (project / "Packages" / "manifest.json").write_text(
                json.dumps({"dependencies": {"com.unity.addressables": "2.0.0"}}), encoding="utf-8"
            )
            output = CodeGenerator().generate_for_request(
                "Addressable prefab yukle", UnityExpertise(project)
            )

            self.assertEqual(output["type"], "unity_template")
            self.assertEqual(output["pipeline"], "URP")
            self.assertIn("Addressables.ReleaseInstance", output["code"])

    def test_incompatible_pipeline_request_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "ProjectSettings").mkdir()
            (project / "ProjectSettings" / "GraphicsSettings.asset").write_text(
                "UniversalRenderPipeline", encoding="utf-8"
            )

            output = CodeGenerator().generate_for_request("HDRP materyal olustur", UnityExpertise(project))

            self.assertEqual(output["type"], "blocked")
            self.assertEqual(output["pipeline"], "URP")

    def test_generator_has_templates_for_core_unity_domains(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            expertise = UnityExpertise(temp_dir)
            cases = {
                "Rigidbody force ekle": "physics",
                "UI canvas score goster": "ui",
                "Timeline playable baslat": "timeline",
                "prefab instantiate et": "prefab",
            }

            for request, topic in cases.items():
                with self.subTest(request=request):
                    output = CodeGenerator().generate_for_request(request, expertise)
                    self.assertEqual(output["type"], "unity_template")
                    self.assertEqual(output["topic"], topic)

    def test_generator_has_a_template_for_every_expertise_domain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "ProjectSettings").mkdir()
            (project / "Packages").mkdir()
            (project / "ProjectSettings" / "GraphicsSettings.asset").write_text(
                "UniversalRenderPipeline", encoding="utf-8"
            )
            (project / "Packages" / "manifest.json").write_text(
                json.dumps({"dependencies": {"com.unity.addressables": "2.0.0"}}), encoding="utf-8"
            )
            expertise = UnityExpertise(project)
            requests = {
                "scene component": "scene", "prefab instantiate": "prefab",
                "rigidbody force": "physics", "timeline playable": "timeline",
                "addressable prefab": "addressables", "shader urp": "rendering",
                "materyal renderer": "material", "animator animation": "animation",
                "canvas ui": "ui", "scriptableobject configuration": "scriptableobject",
                "build player": "build", "import asset": "asset_pipeline",
                "audio sound": "audio", "navmesh agent": "navigation",
            }

            for request, topic in requests.items():
                with self.subTest(topic=topic):
                    output = CodeGenerator().generate_for_request(request, expertise)
                    self.assertEqual(output["type"], "unity_template")
                    self.assertEqual(output["topic"], topic)


if __name__ == "__main__":
    unittest.main()
