import sqlite3
import json

class ScriptDatabase:

    def __init__(self, db="AIEngineer.db"):

        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()

        self.cur.execute("""
        DROP TABLE IF EXISTS script_index
        """)

        self.cur.execute("""
        CREATE TABLE script_index(

            class_name TEXT PRIMARY KEY,
            path TEXT,

            base_class TEXT,

            using_namespaces TEXT,

            fields TEXT,

            methods TEXT,

            serialize_fields TEXT,

            get_components TEXT,

            find_object_of_type TEXT,

            coroutines TEXT,

            instantiate_count INTEGER,

            destroy_count INTEGER

        )
        """)

        self.conn.commit()

    def clear(self):

        self.cur.execute(
            "DELETE FROM script_index"
        )

        self.conn.commit()

    def insert(self, script, analysis):

        self.cur.execute("""

        INSERT OR REPLACE INTO script_index
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)

        """,(

            script["name"],
            script["path"],

            analysis["base_class"],

            json.dumps(
                analysis["using"]
            ),

            json.dumps(
                script["fields"]
            ),

            json.dumps(
                script["methods"]
            ),

            json.dumps(
                analysis["serialize_fields"]
            ),

            json.dumps(
                analysis["get_components"]
            ),

            json.dumps(
                analysis["find_object_of_type"]
            ),

            json.dumps(
                analysis["coroutines"]
            ),

            analysis["instantiate"],

            analysis["destroy"]

        ))

        self.conn.commit()

    def count(self):

        self.cur.execute(
            "SELECT COUNT(*) FROM script_index"
        )

        return self.cur.fetchone()[0]
