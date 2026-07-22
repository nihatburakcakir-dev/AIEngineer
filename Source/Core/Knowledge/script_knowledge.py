import sqlite3
import json
import os

class ScriptKnowledge:

    def __init__(
        self,
        db="AIEngineer.db",
        project_root=""
    ):

        self.conn = sqlite3.connect(db)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

        self.project_root = project_root

    def full_path(self, relative_path):

        if self.project_root == "":
            return relative_path

        return os.path.join(
            self.project_root,
            relative_path
        )

    def classes(self):

        self.cur.execute(
            "SELECT class_name FROM script_index ORDER BY class_name"
        )

        return [r["class_name"] for r in self.cur.fetchall()]

    def find_script(self, name):

        row = self.find_class(name)

        if row is None:
            return None

        return row["path"]

    def find_class(self, name):

        self.cur.execute(
            "SELECT * FROM script_index WHERE class_name=?",
            (name,)
        )

        row = self.cur.fetchone()

        if row is None:
            return None

        return {
            "class": row["class_name"],
            "path": row["path"],
            "full_path": self.full_path(row["path"]),
            "fields": json.loads(row["fields"]),
            "methods": json.loads(row["methods"])
        }

    def fields_of(self, name):

        obj = self.find_class(name)

        if obj is None:
            return []

        return obj["fields"]

    def methods_of(self, name):

        obj = self.find_class(name)

        if obj is None:
            return []

        return obj["methods"]

    def find_field(self, field):

        result = []

        self.cur.execute(
            "SELECT * FROM script_index"
        )

        for row in self.cur.fetchall():

            fields = json.loads(row["fields"])

            for t, n in fields:

                if n.lower() == field.lower():

                    result.append({
                        "class": row["class_name"],
                        "type": t,
                        "field": n,
                        "path": row["path"],
                        "full_path": self.full_path(row["path"])
                    })

        return result

    def find_method(self, method):

        result = []

        self.cur.execute(
            "SELECT * FROM script_index"
        )

        for row in self.cur.fetchall():

            methods = json.loads(row["methods"])

            if method in methods:

                result.append(row["class_name"])

        return result
