import re
from pathlib import Path


class PerformanceTool:
    name = "Performance"

    RULES = (
        ("update_get_component", r"\bUpdate\s*\([^)]*\)\s*\{[\s\S]*?GetComponent\s*<", "Cache component references in Awake."),
        ("update_instantiate", r"\bUpdate\s*\([^)]*\)\s*\{[\s\S]*?Instantiate\s*\(", "Use object pooling instead of Instantiate in Update."),
        ("update_destroy", r"\bUpdate\s*\([^)]*\)\s*\{[\s\S]*?Destroy\s*\(", "Avoid Destroy in Update; pool objects instead."),
        ("update_string_concat", r"\bUpdate\s*\([^)]*\)\s*\{[\s\S]*?\w+\s*\+\s*\w+", "Avoid per-frame string concatenation; cache or use StringBuilder."),
    )

    def analyze(self, file_path):
        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        findings = []
        for rule, expression, recommendation in self.RULES:
            match = re.search(expression, source, re.MULTILINE)
            if match:
                findings.append({"rule": rule, "severity": "MEDIUM", "line": source.count("\n", 0, match.start()) + 1, "recommendation": recommendation})
        return findings

    def propose_fixes(self, file_path):
        proposals = []
        for finding in self.analyze(file_path):
            operation = {
                "update_get_component": "cache_component_in_awake",
                "update_instantiate": "replace_with_object_pool",
                "update_destroy": "replace_with_object_pool",
                "update_string_concat": "remove_per_frame_allocation",
            }[finding["rule"]]
            proposals.append({**finding, "operation": operation, "risk": "MEDIUM"})
        return proposals
