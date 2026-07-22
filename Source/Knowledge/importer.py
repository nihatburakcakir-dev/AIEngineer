from Source.Knowledge.database import Database


class Importer:

    def __init__(self):

        self.db = Database()


    def import_scene(self, objects):

        self.db.clear_scene()

        for obj in objects:

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

            self.db.insert_scene_object(obj)

        self.db.commit()

        return self.db.scene_count()
