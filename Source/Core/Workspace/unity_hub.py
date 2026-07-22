import json
import os
from pathlib import Path

class UnityHub:

    def __init__(self):

        self.locations = [

            Path(os.getenv("APPDATA", "")) / "UnityHub" / "secondaryInstallPath.json",

            Path(os.getenv("APPDATA", "")) / "UnityHub" / "projects-v1.json",

            Path(os.getenv("APPDATA", "")) / "UnityHub" / "projects.json"
        ]

    def project_files(self):

        return [f for f in self.locations if f.exists()]

    def projects(self):

        result = []

        for file in self.project_files():

            if "projects" not in file.name.lower():

                continue

            try:

                with open(
                    file,
                    encoding="utf-8-sig"
                ) as f:

                    data = json.load(f)

            except:

                continue

            self.extract(data, result)

        unique = []

        seen = set()

        for p in result:

            if p not in seen:

                seen.add(p)

                unique.append(p)

        return unique

    def extract(self, obj, result):

        if isinstance(obj, dict):

            for k, v in obj.items():

                if k.lower() == "path":

                    if isinstance(v, str):

                        if os.path.exists(v):

                            result.append(v)

                self.extract(v, result)

        elif isinstance(obj, list):

            for item in obj:

                self.extract(item, result)
