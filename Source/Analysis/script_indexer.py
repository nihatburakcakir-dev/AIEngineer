import re
from pathlib import Path

class ScriptIndexer:

    IGNORE = [
        "TextMesh Pro",
        "Samples",
        "Example",
        "Examples",
        "_Recovery",
        "Yughues",
        "Casual Game Sounds",
        "Matthew Guz",
        "Hovl Studio"
    ]

    UNITY_EVENTS = {
        "Awake",
        "Start",
        "Update",
        "LateUpdate",
        "FixedUpdate",
        "OnEnable",
        "OnDisable",
        "OnDestroy",
        "OnTriggerEnter",
        "OnTriggerExit",
        "OnCollisionEnter",
        "OnCollisionExit"
    }

    def __init__(self, project_path):
        self.project_path = Path(project_path)

    def ignored(self, path):
        ignored_names = {name.casefold() for name in self.IGNORE}
        return any(part.casefold() in ignored_names for part in Path(path).parts)

    def scan(self):

        assets = self.project_path / "Assets"

        if not assets.is_dir():
            raise ValueError(
                f"Unity project '{self.project_path}' does not contain an Assets directory."
            )

        scripts = []

        for file in (self.project_path / "Assets").rglob("*.cs"):

            if self.ignored(file):
                continue

            text = file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            cls = re.search(r'class\s+(\w+)', text)

            if not cls:
                continue

            fields = re.findall(
                r'public\s+([\w<>\[\]]+)\s+(\w+)\s*(?:=|;)',
                text
            )

            methods = set()

            for m in re.findall(
                r'(?:public|private|protected|internal)?\s*(?:virtual\s+|override\s+|static\s+)?(?:IEnumerator|void|bool|int|float|double|string|[\w<>\[\]]+)\s+(\w+)\s*\(',
                text
            ):
                methods.add(m)

            for evt in self.UNITY_EVENTS:
                if re.search(r'\b' + evt + r'\s*\(', text):
                    methods.add(evt)

            scripts.append({
                "name": cls.group(1),
                "path": file.relative_to(self.project_path).as_posix(),
                "fields": fields,
                "methods": sorted(methods)
            })

        return sorted(scripts, key=lambda script: (script["path"].casefold(), script["name"].casefold()))
