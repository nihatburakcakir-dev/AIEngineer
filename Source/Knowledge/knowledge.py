from Source.Knowledge.scanner import Scanner
from Source.Knowledge.indexer import Indexer
from Source.Knowledge.database import Database


class Knowledge:

    def __init__(self, project_path):

        self.project_path = project_path

        self.scanner = Scanner(project_path)

        self.indexer = Indexer()

        self.database = Database()

    def build(self):

        self.database.clear()

        files = self.scanner.scan()

        for file in files:

            item = dict(file)

            if item["type"] == "script":

                try:

                    full_path = (
                        self.project_path
                        + "\\"
                        + item["path"]
                    )

                    item["analysis"] = (
                        self.indexer.index_script(
                            full_path
                        )
                    )

                except Exception as e:

                    item["analysis"] = {
                        "error": str(e)
                    }

            self.database.insert(item)

        self.database.commit()

        return self.database.count()
