import re
from pathlib import Path

class CodeAnalyzer:

    def __init__(self, project_path):
        self.project_path = Path(project_path)

    def analyze(self, relative_path):

        file = self.project_path / relative_path

        text = file.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        using = sorted(set(
            re.findall(r'using\s+([\w\.]+)\s*;', text)
        ))

        inherit = re.search(
            r'class\s+\w+\s*:\s*([\w<>, ]+)',
            text
        )

        serialize = re.findall(
            r'\[SerializeField\]\s*private\s+([\w<>\[\]]+)\s+(\w+)',
            text
        )

        getcomponents = sorted(set(
            re.findall(r'GetComponent<([\w<>]+)>', text)
        ))

        findobjects = sorted(set(
            re.findall(r'FindObjectOfType<([\w<>]+)>', text)
        ))

        instantiate = sorted(set(
            re.findall(r'Instantiate\s*\(', text)
        ))

        destroy = sorted(set(
            re.findall(r'Destroy\s*\(', text)
        ))

        coroutines = sorted(set(
            re.findall(r'StartCoroutine\s*\(\s*(\w+)', text)
        ))

        return {

            "base_class":
                inherit.group(1).strip()
                if inherit else None,

            "using": using,

            "serialize_fields": serialize,

            "get_components": getcomponents,

            "find_object_of_type": findobjects,

            "instantiate": len(instantiate),

            "destroy": len(destroy),

            "coroutines": coroutines
        }
