import json

from pathlib import Path


class WorkflowLoader:

    def __init__(self):

        self.folder = Path("Workflows")


    def load(self, intent):

        file = self.folder / f"{intent}.json"

        if not file.exists():

            raise FileNotFoundError(file)

        with open(
            file,
            encoding="utf-8-sig"
        ) as f:

            return json.load(f)


    def list(self):

        return [

            f.stem

            for f in self.folder.glob("*.json")

        ]
