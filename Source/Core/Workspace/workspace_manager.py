import json
import os
from pathlib import Path

class WorkspaceManager:

    def __init__(self):

        self.config_file = "ai_config.json"

        self.data = {}

        if os.path.exists(self.config_file):

            with open(
                self.config_file,
                encoding="utf-8-sig"
            ) as f:

                self.data = json.load(f)

    def save(self):

        with open(
            self.config_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.data,
                f,
                indent=4
            )

    def find_unity_versions(self):

        root = Path(
            r"C:\Program Files\Unity\Hub\Editor"
        )

        if not root.exists():

            return []

        versions = []

        for folder in root.iterdir():

            exe = folder / "Editor" / "Unity.exe"

            if exe.exists():

                versions.append({

                    "version": folder.name,

                    "path": str(exe)

                })

        return versions

    def set_unity(self, path):

        self.data["unity_path"] = path

        self.save()

    def unity_path(self):

        return self.data.get(
            "unity_path",
            ""
        )
