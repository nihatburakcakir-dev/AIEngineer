from pathlib import Path


SCAN_ROOTS = [
    "Assets"
]


IGNORE_FOLDERS = {
    "Library",
    "Temp",
    "Obj",
    "Logs",
    "Build",
    "Builds",
    ".git",
    ".vs",
    ".idea",
    "UserSettings",
    "PackageCache"
}


EXTENSIONS = {
    ".cs": "script",
    ".prefab": "prefab",
    ".unity": "scene",
    ".mat": "material",
    ".png": "sprite",
    ".jpg": "sprite",
    ".jpeg": "sprite",
    ".wav": "audio",
    ".mp3": "audio",
    ".anim": "animation",
    ".controller": "animator",
    ".shader": "shader",
    ".asset": "asset"
}


class Scanner:

    def __init__(self, project_path):

        self.project = Path(project_path)

    def scan(self):

        files = []

        for root in SCAN_ROOTS:

            root_path = self.project / root

            if not root_path.exists():
                continue

            for file in root_path.rglob("*"):

                if not file.is_file():
                    continue

                if any(folder in file.parts for folder in IGNORE_FOLDERS):
                    continue

                ext = file.suffix.lower()

                if ext not in EXTENSIONS:
                    continue

                files.append({

                    "name": file.stem,

                    "type": EXTENSIONS[ext],

                    "extension": ext,

                    "path": str(
                        file.relative_to(self.project)
                    ),

                    "folder": str(
                        file.parent.relative_to(self.project)
                    ),

                    "size": file.stat().st_size,

                    "modified":
                        file.stat().st_mtime
                })

        return files
