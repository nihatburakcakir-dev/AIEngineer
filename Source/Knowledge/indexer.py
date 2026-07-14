import re
from pathlib import Path


CLASS = re.compile(
    r"class\s+([A-Za-z_][A-Za-z0-9_]*)"
)

METHOD = re.compile(
    r"(?:public|private|protected|internal)\s+.*?\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
)

FIELD = re.compile(
    r"(?:public|private|protected|internal)\s+[\w<>\[\]]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|;)"
)


class Indexer:

    def index_script(self, file_path):

        text = Path(file_path).read_text(
            encoding="utf-8",
            errors="ignore"
        )

        cls = CLASS.search(text)

        return {

            "class":
                cls.group(1)
                if cls
                else None,

            "methods":
                METHOD.findall(text),

            "fields":
                FIELD.findall(text)
        }
