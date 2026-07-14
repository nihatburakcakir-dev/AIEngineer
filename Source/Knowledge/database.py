import sqlite3
import json


class Database:

    def __init__(self, db_path="knowledge.db"):

        self.conn = sqlite3.connect(db_path)

        self.create_tables()


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

            tag TEXT,

            layer TEXT,

            position TEXT,

            rotation TEXT,

            scale TEXT,

            components TEXT

        )

        """)

        self.conn.commit()


    def clear(self):

        self.conn.execute(
            "DELETE FROM files"
        )

        self.conn.commit()


    def clear_scene(self):

        self.conn.execute(
            "DELETE FROM scene_objects"
        )

        self.conn.commit()


    def insert(self, item):

        self.conn.execute(

            """

            INSERT OR REPLACE INTO files(

                name,
                type,
                extension,
                path,
                folder,
                size,
                modified,
                analysis

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

                json.dumps(
                    item.get("analysis", {})
                )

            )

        )


    def insert_scene_object(self, obj):

        if isinstance(obj, str):

            obj = {

                "name": obj,

                "path": "",

                "tag": "",

                "layer": "",

                "position": {},

                "rotation": {},

                "scale": {},

                "components": []

            }

        self.conn.execute(

            """

            INSERT INTO scene_objects(

                name,
                path,
                tag,
                layer,
                position,
                rotation,
                scale,
                components

            )

            VALUES(?,?,?,?,?,?,?,?)

            """,

            (

                obj.get("name"),

                obj.get("path"),

                obj.get("tag"),

                obj.get("layer"),

                json.dumps(obj.get("position")),

                json.dumps(obj.get("rotation")),

                json.dumps(obj.get("scale")),

                json.dumps(obj.get("components"))

            )

        )


    def commit(self):

        self.conn.commit()


    def count(self):

        cur = self.conn.execute(

            "SELECT COUNT(*) FROM files"

        )

        return cur.fetchone()[0]


    def scene_count(self):

        cur = self.conn.execute(

            "SELECT COUNT(*) FROM scene_objects"

        )

        return cur.fetchone()[0]
