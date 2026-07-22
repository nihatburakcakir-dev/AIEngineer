import re
from pathlib import Path

from Source.Analysis.project_indexer import ProjectIndexer
from Source.Analysis.script_indexer import ScriptIndexer
from Source.Core.Knowledge.project_graph import ProjectGraph


class ProjectSummary:
    """Produces a deterministic, inspectable explanation of a Unity project."""

    def __init__(self, project_path, db_path="AIEngineer.db"):
        self.project_path = Path(project_path)
        self.graph = ProjectGraph(db_path)

    def describe(self):
        assets = ProjectIndexer(self.project_path).scan()
        scripts = ScriptIndexer(self.project_path).scan()
        graph = self.graph.build_from_project(self.project_path)
        scenes = assets["Scenes"]
        prefabs = assets["Prefabs"]
        script_names = [item["name"] for item in scripts]
        scene_objects = self._scene_objects(scenes)
        object_count = sum(len(objects) for objects in scene_objects.values())

        summary = (
            f"Unity projesi {len(scenes)} sahne, {len(prefabs)} prefab ve "
            f"{len(scripts)} C# script içeriyor; sahnelerde {object_count} GameObject bulundu. "
            f"Varlık grafiğinde {graph['nodes']} düğüm ve {graph['edges']} referans var."
        )
        return {
            "summary": summary,
            "assets": assets,
            "scripts": script_names,
            "scenes": scenes,
            "prefabs": prefabs,
            "scene_objects": scene_objects,
            "graph": graph,
        }

    def _scene_objects(self, scene_paths):
        result = {}
        pattern = re.compile(r"--- !u!1 &[^\r\n]+\r?\nGameObject:\s*\r?\n(?:.*\r?\n)*?\s+m_Name:\s*(.+)")
        for relative_path in scene_paths:
            scene_file = self.project_path / Path(relative_path)
            content = scene_file.read_text(encoding="utf-8", errors="ignore")
            result[relative_path] = [name.strip() for name in pattern.findall(content)]
        return result

    def close(self):
        self.graph.close()
