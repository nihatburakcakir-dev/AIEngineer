"""Regression coverage for FAZ 1's Unity project scanning pipeline."""

import tempfile
import unittest
from pathlib import Path

from Source.Analysis.project_indexer import ProjectIndexer
from Source.Analysis.script_indexer import ScriptIndexer


class ProjectIndexingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name)
        self.assets = self.project / "Assets"
        self.assets.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_asset(self, relative_path, content=""):
        path = self.assets / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_project_indexer_collects_supported_assets_in_stable_order(self):
        self.write_asset("Zebra/Player.cs")
        self.write_asset("Art/Hero.prefab")
        self.write_asset("Art/Grass.mat")
        self.write_asset("Scenes/Main.unity")
        self.write_asset("Art/Icon.PNG")
        self.write_asset("TextMesh Pro/Examples~/Ignored.cs")

        result = ProjectIndexer(self.project).scan()

        self.assertEqual(result["Scripts"], ["Assets/Zebra/Player.cs"])
        self.assertEqual(result["Prefabs"], ["Assets/Art/Hero.prefab"])
        self.assertEqual(result["Materials"], ["Assets/Art/Grass.mat"])
        self.assertEqual(result["Scenes"], ["Assets/Scenes/Main.unity"])
        self.assertEqual(result["Sprites"], ["Assets/Art/Icon.PNG"])

    def test_script_indexer_extracts_unity_script_shape_and_ignores_samples(self):
        self.write_asset(
            "Scripts/PlayerController.cs",
            """using UnityEngine;
public class PlayerController : MonoBehaviour {
    public int score = 0;
    private Rigidbody body;
    void Awake() { }
    public void Jump(float force) { }
}""",
        )
        self.write_asset("Samples/Example.cs", "public class Example { }")

        result = ScriptIndexer(self.project).scan()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "PlayerController")
        self.assertEqual(result[0]["path"], "Assets/Scripts/PlayerController.cs")
        self.assertIn(("int", "score"), result[0]["fields"])
        self.assertIn("Awake", result[0]["methods"])
        self.assertIn("Jump", result[0]["methods"])

    def test_indexers_reject_a_path_that_is_not_a_unity_project(self):
        missing_assets = self.project / "not-a-project"

        with self.assertRaises(ValueError):
            ProjectIndexer(missing_assets).scan()
        with self.assertRaises(ValueError):
            ScriptIndexer(missing_assets).scan()


if __name__ == "__main__":
    unittest.main()
