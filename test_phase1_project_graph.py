"""Regression coverage for FAZ 1's Unity asset relationship graph."""

import tempfile
import unittest
from pathlib import Path

from Source.Core.Knowledge.project_graph import ProjectGraph
from Source.Core.Knowledge.project_summary import ProjectSummary


class ProjectGraphTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name)
        self.assets = self.project / "Assets"
        for directory in ("Scripts", "Prefabs", "Scenes"):
            (self.assets / directory).mkdir(parents=True)
        (self.assets / "Scripts" / "Player.cs").write_text("public class Player {}", encoding="utf-8")
        (self.assets / "Scripts" / "Player.cs.meta").write_text("guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", encoding="utf-8")
        (self.assets / "Prefabs" / "Player.prefab").write_text(
            "m_Script: {fileID: 11500000, guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, type: 3}", encoding="utf-8"
        )
        (self.assets / "Prefabs" / "Player.prefab.meta").write_text("guid: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", encoding="utf-8")
        (self.assets / "Scenes" / "Main.unity").write_text(
            """--- !u!1 &1
GameObject:
  m_Name: MainCamera
m_SourcePrefab: {fileID: 100100000, guid: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb, type: 3}""", encoding="utf-8"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_resolves_prefab_and_scene_guid_references(self):
        graph = ProjectGraph(str(self.project / "graph.db"))
        self.assertEqual(graph.build_from_project(self.project), {"nodes": 3, "edges": 2})
        self.assertEqual(graph.prefabs_using_script("Assets/Scripts/Player.cs"), ["Assets/Prefabs/Player.prefab"])
        self.assertEqual(graph.references_from("Assets/Scenes/Main.unity"), ["Assets/Prefabs/Player.prefab"])
        graph.close()

    def test_summary_reports_scanned_project_contents(self):
        summary = ProjectSummary(self.project, str(self.project / "summary.db"))
        result = summary.describe()
        self.assertIn("1 sahne, 1 prefab ve 1 C# script", result["summary"])
        self.assertEqual(result["graph"], {"nodes": 3, "edges": 2})
        self.assertEqual(result["scene_objects"], {"Assets/Scenes/Main.unity": ["MainCamera"]})
        summary.close()


if __name__ == "__main__":
    unittest.main()
