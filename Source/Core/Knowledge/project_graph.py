import sqlite3
import json

import re
from pathlib import Path


class ProjectGraph:

    def __init__(self, db="AIEngineer.db"):

        self.conn = sqlite3.connect(db)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.cur.executescript("""
            CREATE TABLE IF NOT EXISTS project_graph_nodes (
                path TEXT PRIMARY KEY,
                asset_type TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS project_graph_edges (
                source_path TEXT NOT NULL,
                target_path TEXT NOT NULL,
                relation TEXT NOT NULL,
                PRIMARY KEY (source_path, target_path, relation)
            );
            CREATE INDEX IF NOT EXISTS project_graph_target_idx
                ON project_graph_edges(target_path);
        """)
        self.conn.commit()

    def build_from_project(self, project_path):
        """Resolve Unity YAML GUIDs into scene/prefab/script asset links."""
        project_path = Path(project_path)
        assets = project_path / "Assets"
        if not assets.is_dir():
            raise ValueError(f"Unity project '{project_path}' does not contain an Assets directory.")

        asset_types = {
            ".cs": "Script", ".prefab": "Prefab", ".unity": "Scene",
            ".mat": "Material", ".asset": "ScriptableObject", ".controller": "Animator",
            ".anim": "Animation", ".shader": "Shader", ".shadergraph": "Shader",
            ".png": "Image", ".jpg": "Image", ".jpeg": "Image", ".fbx": "Model",
            ".wav": "Audio", ".mp3": "Audio", ".ogg": "Audio",
        }
        guid_pattern = re.compile(r"\bguid:\s*([0-9a-fA-F]{32})\b")
        guid_to_path, nodes = {}, []

        for file_path in assets.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() == ".meta":
                continue
            asset_type = asset_types.get(file_path.suffix.lower())
            if asset_type is None:
                continue
            relative = file_path.relative_to(project_path).as_posix()
            nodes.append((file_path, relative, asset_type))
            meta_path = Path(f"{file_path}.meta")
            if meta_path.is_file():
                match = guid_pattern.search(meta_path.read_text(encoding="utf-8", errors="ignore"))
                if match:
                    guid_to_path[match.group(1).lower()] = relative

        self.cur.execute("DELETE FROM project_graph_edges")
        self.cur.execute("DELETE FROM project_graph_nodes")
        self.cur.executemany(
            "INSERT INTO project_graph_nodes(path, asset_type) VALUES (?, ?)",
            [(relative, asset_type) for _, relative, asset_type in nodes],
        )

        edges = set()
        reference_types = {"Scene", "Prefab", "ScriptableObject", "Material", "Animator"}
        for file_path, relative, asset_type in nodes:
            if asset_type not in reference_types:
                continue
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for guid in guid_pattern.findall(content):
                target = guid_to_path.get(guid.lower())
                if target and target != relative:
                    edges.add((relative, target, "references"))
        self.cur.executemany(
            "INSERT INTO project_graph_edges(source_path, target_path, relation) VALUES (?, ?, ?)",
            sorted(edges),
        )
        self.conn.commit()
        return {"nodes": len(nodes), "edges": len(edges)}

    def references_from(self, asset_path):
        self.cur.execute(
            "SELECT target_path FROM project_graph_edges WHERE source_path=? ORDER BY target_path",
            (str(asset_path).replace("\\", "/"),),
        )
        return [row["target_path"] for row in self.cur.fetchall()]

    def assets_using(self, asset_path, asset_type=None):
        query = (
            "SELECT edges.source_path FROM project_graph_edges AS edges "
            "JOIN project_graph_nodes AS nodes ON nodes.path=edges.source_path "
            "WHERE edges.target_path=?"
        )
        params = [str(asset_path).replace("\\", "/")]
        if asset_type:
            query += " AND nodes.asset_type=?"
            params.append(asset_type)
        self.cur.execute(query + " ORDER BY edges.source_path", params)
        return [row["source_path"] for row in self.cur.fetchall()]

    def prefabs_using_script(self, script_path):
        return self.assets_using(script_path, "Prefab")

    def close(self):
        self.conn.close()

    def classes(self):

        self.cur.execute(
            "SELECT class_name FROM script_index ORDER BY class_name"
        )

        return [r["class_name"] for r in self.cur.fetchall()]

    def inherits(self, cls):

        self.cur.execute(
            "SELECT base_class FROM script_index WHERE class_name=?",
            (cls,)
        )

        row = self.cur.fetchone()

        return row["base_class"] if row else None

    def uses(self, cls):

        self.cur.execute(
            """
            SELECT get_components
            FROM script_index
            WHERE class_name=?
            """,
            (cls,)
        )

        row = self.cur.fetchone()

        if row is None:
            return []

        return json.loads(row["get_components"])

    def serialize_fields(self, cls):

        self.cur.execute(
            """
            SELECT serialize_fields
            FROM script_index
            WHERE class_name=?
            """,
            (cls,)
        )

        row = self.cur.fetchone()

        if row is None:
            return []

        return json.loads(row["serialize_fields"])

    def namespaces(self, cls):

        self.cur.execute(
            """
            SELECT using_namespaces
            FROM script_index
            WHERE class_name=?
            """,
            (cls,)
        )

        row = self.cur.fetchone()

        if row is None:
            return []

        return json.loads(row["using_namespaces"])

    def find_component(self, component):

        result = []

        self.cur.execute(
            """
            SELECT class_name,get_components
            FROM script_index
            """
        )

        for row in self.cur.fetchall():

            comps = json.loads(row["get_components"])

            if component in comps:
                result.append(row["class_name"])

        return result

    def find_base(self, base):

        self.cur.execute(
            """
            SELECT class_name
            FROM script_index
            WHERE base_class=?
            """,
            (base,)
        )

        return [r["class_name"] for r in self.cur.fetchall()]
