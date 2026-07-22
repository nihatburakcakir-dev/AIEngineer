import re
from pathlib import Path

from Source.Core.CodeModel.parser import CodeParser


class RefactorTool:
    name = "Refactor"

    def rename_symbol(self, file_path, old_name, new_name, apply=False):
        """Create or apply a scope-agnostic, identifier-safe rename patch."""
        if not re.fullmatch(r"[A-Za-z_]\w*", new_name):
            raise ValueError("New symbol name must be a valid C# identifier.")
        path = Path(file_path)
        source = path.read_text(encoding="utf-8")
        masked = CodeParser._mask_comments_and_strings(source)
        matches = list(re.finditer(rf"\b{re.escape(old_name)}\b", masked))
        updated = source
        for match in reversed(matches):
            updated = updated[:match.start()] + new_name + updated[match.end():]
        count = len(matches)
        result = {"file": str(path), "old_name": old_name, "new_name": new_name, "occurrences": count}
        if apply and count:
            path.write_text(updated, encoding="utf-8")
            result["applied"] = True
        else:
            result["applied"] = False
            result["preview"] = updated
        return result

    def find_duplicate_methods(self, file_path):
        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        pattern = re.compile(r"\b(?:public|private|protected|internal)?\s*(?:static\s+)?(?:void|int|float|string|bool)\s+(\w+)\s*\([^)]*\)\s*\{([^{}]*)\}")
        groups = {}
        for match in pattern.finditer(source):
            normalized = re.sub(r"\s+", " ", match.group(2)).strip()
            groups.setdefault(normalized, []).append(match.group(1))
        return [
            {"methods": names, "recommendation": "Extract the shared body into one private method."}
            for body, names in groups.items() if body and len(names) > 1
        ]

    def extract_method_plan(self, file_path, start_line, end_line, method_name, apply=False):
        if start_line < 1 or end_line < start_line or not re.fullmatch(r"[A-Za-z_]\w*", method_name):
            raise ValueError("Invalid method extraction range or method name.")
        lines = Path(file_path).read_text(encoding="utf-8").splitlines()
        if end_line > len(lines):
            raise ValueError("Extraction range exceeds the file length.")
        result = {
            "file": str(file_path),
            "operation": "extract_method",
            "method_name": method_name,
            "lines": [start_line, end_line],
            "body": "\n".join(lines[start_line - 1:end_line]),
            "requires_review": True,
        }
        if apply:
            body = result["body"]
            indentation = re.match(r"\s*", lines[start_line - 1]).group(0)
            lines[start_line - 1:end_line] = [f"{indentation}{method_name}();"]
            insertion = ["", f"{indentation}private void {method_name}()", f"{indentation}{{"]
            insertion.extend(f"{indentation}    {line.strip()}" for line in body.splitlines())
            insertion.append(f"{indentation}}}")
            lines[-1:-1] = insertion
            Path(file_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
            result["applied"] = True
        else:
            result["applied"] = False
        return result
