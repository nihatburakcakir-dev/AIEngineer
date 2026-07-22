import json
import tempfile
import unittest
from pathlib import Path

from Source.Knowledge.unity_expertise import UnityExpertise


class UnityExpertiseTests(unittest.TestCase):
    def test_detects_urp_and_retrieves_pipeline_specific_rule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "ProjectSettings").mkdir()
            (project / "Packages").mkdir()
            (project / "ProjectSettings" / "GraphicsSettings.asset").write_text(
                "UnityEngine.Rendering.Universal.UniversalRenderPipeline", encoding="utf-8"
            )
            (project / "Packages" / "manifest.json").write_text(json.dumps({"dependencies": {}}), encoding="utf-8")

            expertise = UnityExpertise(project)
            rules = expertise.retrieve("URP shader material olustur")

            self.assertEqual(expertise.render_pipeline(), "URP")
            self.assertTrue(any("URP compatible" in rule for result in rules for rule in result["rules"]))

    def test_retrieves_physics_practices(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            rules = UnityExpertise(temp_dir).retrieve("Rigidbody force ekle")
            self.assertTrue(any(result["topic"] == "physics" for result in rules))

    def test_rejects_hdrp_material_request_for_urp_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "ProjectSettings").mkdir()
            (project / "ProjectSettings" / "GraphicsSettings.asset").write_text(
                "UniversalRenderPipeline", encoding="utf-8"
            )

            recommendation = UnityExpertise(project).recommend("HDRP materyal olustur")

            self.assertFalse(recommendation["allowed"])
            self.assertIn("incompatible", recommendation["reason"])

    def test_addressables_requires_package_before_conversion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            recommendation = UnityExpertise(temp_dir).recommend("bu prefab addressable yap")

            self.assertFalse(recommendation["allowed"])
            self.assertEqual(recommendation["action"], "mark_addressable")

    def test_all_phase_three_expertise_packages_are_available(self):
        expected_topics = {
            "scene", "prefab", "physics", "timeline", "addressables", "rendering",
            "material", "animation", "ui", "scriptableobject", "build",
            "asset_pipeline", "audio", "navigation",
        }

        self.assertTrue(expected_topics.issubset(set(__import__("Source.Knowledge.unity_expertise", fromlist=["EXPERTISE"]).EXPERTISE)))

    def test_context_carries_retrieved_unity_documentation(self):
        context = UnityExpertise(".").context_for("physics", [{"title": "Rigidbody", "section": "AddForce"}])

        self.assertEqual(context["documentation"], [{"title": "Rigidbody", "section": "AddForce"}])

    def test_each_expertise_package_has_a_documented_pitfall(self):
        from Source.Knowledge.unity_expertise import EXPERTISE, PITFALLS

        self.assertEqual(set(EXPERTISE), set(PITFALLS))
        self.assertTrue(all(PITFALLS[topic] for topic in EXPERTISE))


if __name__ == "__main__":
    unittest.main()
