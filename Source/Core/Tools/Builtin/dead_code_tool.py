from pathlib import Path
import re

from Source.Core.CodeModel.parser import CodeParser


class DeadCodeTool:
    name = "DeadCode"

    def find_unreferenced_scripts(self, project_graph, project_path):
        """Return script assets that have no inbound scene/prefab/asset graph edge."""
        project_path = Path(project_path)
        candidates = []
        project_graph.cur.execute("SELECT path FROM project_graph_nodes WHERE asset_type='Script' ORDER BY path")
        for row in project_graph.cur.fetchall():
            script_path = row["path"]
            if not project_graph.assets_using(script_path):
                candidates.append({"path": script_path, "reason": "No Unity asset graph reference found; inspect before deletion."})
        return candidates

    def find_unreferenced_methods(self, file_path):
        model = CodeParser().parse(file_path)
        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        unity_messages = {"Awake", "Start", "Update", "LateUpdate", "FixedUpdate", "OnEnable", "OnDisable", "OnDestroy"}
        result = []
        for cls in model.classes:
            for method in cls.methods:
                if method.name in unity_messages:
                    continue
                if len(re.findall(rf"\b{re.escape(method.name)}\b", source)) == 1:
                    result.append({"method": method.name, "class": cls.name, "reason": "No in-file call found; inspect overrides, Unity events and reflection before deletion."})
        return result
