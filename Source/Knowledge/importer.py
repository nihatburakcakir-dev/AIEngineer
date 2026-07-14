from Source.Knowledge.database import Database


class Importer:

    def __init__(self):

        self.db = Database()


    def import_scene(self, objects):

        self.db.clear_scene()

        for obj in objects:

            self.db.insert_scene_object(obj)

        self.db.commit()

        return self.db.scene_count()
