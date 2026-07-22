from pathlib import Path

class ProjectIndexer:

    IGNORE = [
        "TextMesh Pro",
        "Samples",
        "Example",
        "Examples",
        "_Recovery",
        "Yughues",
        "Casual Game Sounds"
    ]

    def __init__(self, project_path):
        self.project_path = Path(project_path)

    def ignored(self, path):
        """Return whether a path is inside a known third-party/sample folder."""
        ignored_names = {name.casefold() for name in self.IGNORE}
        return any(part.casefold() in ignored_names for part in Path(path).parts)

    def scan(self):

        data = {
            "Scripts": [],
            "Prefabs": [],
            "Scenes": [],
            "Materials": [],
            "Textures": [],
            "Sprites": [],
            "Animations": [],
            "Animators": [],
            "Shaders": [],
            "Models": [],
            "ScriptableObjects": [],
            "Audio": []
        }

        exts = {
            ".cs":"Scripts",
            ".prefab":"Prefabs",
            ".unity":"Scenes",
            ".mat":"Materials",
            ".png":"Sprites",
            ".jpg":"Textures",
            ".jpeg":"Textures",
            ".tiff":"Textures",
            ".tif":"Textures",
            ".psd":"Textures",
            ".exr":"Textures",
            ".wav":"Audio",
            ".mp3":"Audio",
            ".ogg":"Audio",
            ".anim":"Animations",
            ".controller":"Animators",
            ".overridecontroller":"Animators",
            ".shader":"Shaders",
            ".shadergraph":"Shaders",
            ".fbx":"Models",
            ".obj":"Models",
            ".blend":"Models",
            ".asset":"ScriptableObjects"
        }

        assets = self.project_path / "Assets"

        if not assets.is_dir():
            raise ValueError(
                f"Unity project '{self.project_path}' does not contain an Assets directory."
            )

        for f in assets.rglob("*"):

            if not f.is_file():
                continue

            if self.ignored(f):
                continue

            ext = f.suffix.lower()

            if ext in exts:
                data[exts[ext]].append(f.relative_to(self.project_path).as_posix())

        for files in data.values():
            files.sort(key=str.casefold)

        return data
