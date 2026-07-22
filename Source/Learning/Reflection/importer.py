import json
from pathlib import Path

from Source.Knowledge.database import Database
from Source.Memory.learning_memory import LearningMemory


class ReflectionImporter:

    def __init__(self):

        self.db = Database()


    def import_json(self, file_path):

        file_path = Path(file_path)

        if not file_path.exists():

            print("Reflection file not found.")

            return

        with open(

            file_path,

            "r",

            encoding="utf-8"

        ) as f:

            data = json.load(f)

        self.db.clear_reflection()

        count = 0

        for item in data.get(

            "types",

            []

        ):

            self.db.insert_reflection(

                assembly=item.get(

                    "assembly",

                    ""

                ),

                namespace=item.get(

                    "namespaceName",

                    ""

                ),

                class_name=item.get(

                    "className",

                    ""

                ),

                base_class=item.get(

                    "baseClass",

                    ""

                ),

                methods=item.get(

                    "methods",

                    []

                ),

                properties=item.get(

                    "properties",

                    []

                ),

                fields=item.get(

                    "fields",

                    []

                )

            )

            count += 1

        self.db.commit()

        print()
        print("=" * 60)
        print("UNITY REFLECTION IMPORT")
        print("=" * 60)
        print("Imported :", count)
        print()


class LearningMemoryImporter:
    """Imports Phase 9 critiques as reusable Phase 10 lessons."""

    def __init__(self, memory=None):
        self.memory = memory or LearningMemory()

    def import_critique_events(self):
        return self.memory.import_critique_events()


if __name__ == "__main__":

    ReflectionImporter().import_json(

        r"C:\AIEngineer\AIReflection\unity_reflection.json"

    )
