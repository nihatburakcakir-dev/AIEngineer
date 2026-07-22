import sqlite3
import json

class Database:

    def __init__(self, db_path="knowledge.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        self.create_reflection_table()
    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS files(
            id INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,
            extension TEXT,
            path TEXT UNIQUE,
            folder TEXT,
            size INTEGER,
            modified REAL,
            analysis TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS scene_objects(
            id INTEGER PRIMARY KEY,
            name TEXT,
            path TEXT,
            parent TEXT,
            tag TEXT,
            layer TEXT,
            active INTEGER,
            position TEXT,
            rotation TEXT,
            scale TEXT,
            children TEXT,
            components TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS project_assets(
            id INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,
            path TEXT UNIQUE
        )
        """)

        self.conn.commit()

    def clear(self):
        self.conn.execute("DELETE FROM files")
        self.conn.commit()

    def clear_scene(self):
        self.conn.execute("DELETE FROM scene_objects")
        self.conn.commit()

    def clear_project(self):
        self.conn.execute("DELETE FROM project_assets")
        self.conn.commit()

    def insert(self, item):
        self.conn.execute(
            """
            INSERT OR REPLACE INTO files(
                name,type,extension,path,folder,size,modified,analysis
            )
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                item.get("name"),
                item.get("type"),
                item.get("extension"),
                item.get("path"),
                item.get("folder"),
                item.get("size"),
                item.get("modified"),
                json.dumps(item.get("analysis", {}))
            )
        )

    def insert_scene_object(self, obj):
        self.conn.execute(
            """
            INSERT INTO scene_objects(
                name,path,parent,tag,layer,active,
                position,rotation,scale,children,components
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                obj.get("name"),
                obj.get("path"),
                obj.get("parent",""),
                obj.get("tag"),
                obj.get("layer"),
                int(obj.get("active", True)),
                json.dumps(obj.get("position", {})),
                json.dumps(obj.get("rotation", {})),
                json.dumps(obj.get("scale", {})),
                json.dumps(obj.get("children", [])),
                json.dumps(obj.get("components", []))
            )
        )

    def insert_project_asset(self, name, asset_type, path):
        self.conn.execute(
            """
            INSERT OR REPLACE INTO project_assets(
                name,type,path
            )
            VALUES(?,?,?)
            """,
            (name, asset_type, path)
        )

    def commit(self):
        self.conn.commit()

    def count(self):
        return self.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]

    def scene_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM scene_objects").fetchone()[0]

    def project_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM project_assets").fetchone()[0]

    def create_reflection_table(self):

        self.conn.execute("""

        CREATE TABLE IF NOT EXISTS reflection_types(

            id INTEGER PRIMARY KEY,

            assembly TEXT,

            namespace TEXT,

            class_name TEXT,

            base_class TEXT,

            methods TEXT,

            properties TEXT,

            fields TEXT

        )

        """)

        self.conn.commit()


    def clear_reflection(self):

        self.conn.execute(

            "DELETE FROM reflection_types"

        )

        self.conn.commit()


    def insert_reflection(

        self,

        assembly,

        namespace,

        class_name,

        base_class,

        methods,

        properties,

        fields

    ):

        self.conn.execute(

            """

            INSERT INTO reflection_types(

                assembly,

                namespace,

                class_name,

                base_class,

                methods,

                properties,

                fields

            )

            VALUES(?,?,?,?,?,?,?)

            """,

            (

                assembly,

                namespace,

                class_name,

                base_class,

                json.dumps(methods),

                json.dumps(properties),

                json.dumps(fields)

            )

        )


    def reflection_count(self):

        cur=self.conn.execute(

            "SELECT COUNT(*) FROM reflection_types"

        )

        return cur.fetchone()[0]

