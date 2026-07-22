from Source.Knowledge.database import Database
import os

class ProjectImporter:

    def __init__(self):

        self.db=Database()

    def import_project(
        self,
        project
    ):

        self.db.clear_project()

        mapping={

            "prefabs":"Prefab",

            "materials":"Material",

            "textures":"Texture",

            "audio":"Audio",

            "scripts":"Script",

            "animations":"Animation"

        }

        for key,assetType in mapping.items():

            for path in project.get(key,[]):

                self.db.insert_project_asset(

                    os.path.splitext(

                        os.path.basename(path)

                    )[0],

                    assetType,

                    path

                )

        self.db.commit()

        print()

        print("="*60)

        print("PROJECT IMPORT")

        print("="*60)

        print(

            "Asset Count :",

            self.db.project_count()

        )
