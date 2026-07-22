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

            if "analysis" in item and item["analysis"]:

                item["analysis"] = json.loads(
                    item["analysis"]
                )

            rows.append(item)

        return rows


    def scene_objects(self):

        return self._rows(

            """

            SELECT *

            FROM scene_objects

            ORDER BY name

            """

        )


    def scene_object_names(self):

        rows = self.scene_objects()

        return [

            row["name"]

            for row in rows

        ]


    def search_scene_object(

        self,

        name

    ):

        return self._rows(

            """

            SELECT *

            FROM scene_objects

            WHERE name LIKE ?

            """,

            (f"%{name}%",)

        )

    def project_assets(self):

        return self._rows(

            """

            SELECT *

            FROM project_assets

            ORDER BY type,name

            """

        )

    def project_assets_by_type(

        self,

        asset_type

    ):

        return self._rows(

            """

            SELECT *

            FROM project_assets

            WHERE type=?

            ORDER BY name

            """,

            (asset_type,)

        )

