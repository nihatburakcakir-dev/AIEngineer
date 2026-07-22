import re
from pathlib import Path


class BugDetectorTool:
    name = "BugDetector"

    RULES = (
        ("infinite_loop", re.compile(r"\bwhile\s*\(\s*true\s*\)"), "HIGH", "An unconditional while loop can freeze the Unity main thread."),
        ("missing_semicolon", re.compile(r"^\s*(?:public|private|protected)\s+[\w<>\[\]]+\s+\w+\s*=\s*[^;{}]+$", re.MULTILINE), "HIGH", "A field initializer appears to be missing a semicolon."),
        ("update_get_component", re.compile(r"\bUpdate\s*\([^)]*\)\s*\{[\s\S]*?GetComponent\s*<", re.MULTILINE), "MEDIUM", "Cache GetComponent results outside Update."),
    )

    def analyze(self, file_path):
        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        findings = []
        for rule, pattern, severity, message in self.RULES:
            for match in pattern.finditer(source):
                findings.append({"rule": rule, "severity": severity, "line": source.count("\n", 0, match.start()) + 1, "message": message})
        field_pattern = re.compile(r"\bprivate\s+[\w<>\[\]]+\s+(\w+)\s*(?:=[^;]+)?;")
        for match in field_pattern.finditer(source):
            name = match.group(1)
            if len(re.findall(rf"\b{re.escape(name)}\b", source)) == 1:
                findings.append({"rule": "unused_private_field", "severity": "LOW", "line": source.count("\n", 0, match.start()) + 1, "message": "Private field is never read; remove it or use it."})
        return findings

    def propose_fixes(self, file_path):
        """Return reviewable fixes; callers decide whether to apply them."""
        proposals = []
        for finding in self.analyze(file_path):
            if finding["rule"] == "missing_semicolon":
                proposals.append({**finding, "operation": "append_semicolon", "risk": "LOW"})
            elif finding["rule"] == "update_get_component":
                proposals.append({**finding, "operation": "cache_component_in_awake", "risk": "MEDIUM"})
            elif finding["rule"] == "infinite_loop":
                proposals.append({**finding, "operation": "require_exit_condition", "risk": "HIGH"})
        return proposals
