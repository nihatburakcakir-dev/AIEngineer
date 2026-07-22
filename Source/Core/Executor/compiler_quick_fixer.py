"""Conservative compiler fixes applied before asking a language model."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any


class CompilerQuickFixer:
    DIAGNOSTIC = re.compile(r"(?P<file>.+?)\((?P<line>\d+),(?P<column>\d+)\).*?error\s+(?P<code>CS\d+)", re.IGNORECASE)

    def try_repair(self, previous: dict[str, Any], diagnostics: list[str]) -> dict[str, Any] | None:
        repaired = deepcopy(previous)
        operations = repaired.get("operations")
        if not isinstance(operations, list):
            return None
        changes = []
        for diagnostic in diagnostics:
            match = self.DIAGNOSTIC.search(str(diagnostic).replace("\\", "/"))
            if not match or match.group("code").upper() not in {"CS1002", "CS1513"}:
                return None
            operation = self._matching_write(operations, match.group("file"))
            if operation is None:
                return None
            content = str(operation.get("content", ""))
            fixed = self._fix(content, int(match.group("line")), match.group("code").upper())
            if fixed is None:
                return None
            operation["content"] = fixed
            changes.append(f"{match.group('code').upper()} fixed in {operation.get('path')}")
        if not changes:
            return None
        repaired["requestId"] = str(repaired.get("requestId", "repair")) + "-quickfix"
        repaired["summary"] = "Compiler-guided repair: " + "; ".join(changes)
        repaired["model"] = "compiler-rule-engine"
        repaired["explanation"] = list(repaired.get("explanation", [])) + changes
        repaired["warnings"] = list(repaired.get("warnings", []))
        return repaired

    @staticmethod
    def _matching_write(operations: list[dict[str, Any]], diagnostic_path: str) -> dict[str, Any] | None:
        diagnostic = diagnostic_path.replace("\\", "/").casefold()
        for operation in operations:
            if not isinstance(operation, dict) or operation.get("kind") != "write_text":
                continue
            path = str(operation.get("path", "")).replace("\\", "/").casefold()
            if path and (diagnostic.endswith(path) or path.endswith(diagnostic)):
                return operation
        return None

    @staticmethod
    def _fix(content: str, line_number: int, code: str) -> str | None:
        lines = content.splitlines()
        if code == "CS1513":
            return content.rstrip() + "\n}\n"
        index = line_number - 1
        if index < 0 or index >= len(lines):
            return None
        line = lines[index]
        stripped = line.rstrip()
        if not stripped or stripped.endswith((";", "{", "}", ":")):
            return None
        comment = stripped.find("//")
        if comment >= 0:
            before, after = stripped[:comment].rstrip(), stripped[comment:]
            lines[index] = before + "; " + after
        else:
            lines[index] = stripped + ";"
        return "\n".join(lines) + ("\n" if content.endswith("\n") else "")
