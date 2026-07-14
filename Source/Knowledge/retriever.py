import sqlite3
import json


class Retriever:

    def __init__(self, db_path="knowledge.db"):

        self.conn = sqlite3.connect(db_path)

        self.conn.row_factory = sqlite3.Row

    def _rows(self, sql, params=()):

        cur = self.conn.execute(sql, params)

        rows = []

        for row in cur.fetchall():

            item = dict(row)

            if item["analysis"]:
                item["analysis"] = json.loads(item["analysis"])

            rows.append(item)

        return rows

    def search_name(self, name):

        return self._rows(

            "SELECT * FROM files WHERE name LIKE ?",

            (f"%{name}%",)

        )

    def search_type(self, asset_type):

        return self._rows(

            "SELECT * FROM files WHERE type=?",

            (asset_type,)

        )

    def search_folder(self, folder):

        return self._rows(

            "SELECT * FROM files WHERE folder LIKE ?",

            (f"%{folder}%",)

        )

    def search_class(self, class_name):

        rows = self._rows(

            "SELECT * FROM files WHERE type='script'"

        )

        result = []

        for row in rows:

            analysis = row.get("analysis", {})

            if analysis.get("class") == class_name:

                result.append(row)

        return result
