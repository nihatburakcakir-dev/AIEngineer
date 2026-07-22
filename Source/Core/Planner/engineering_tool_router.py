class EngineeringToolRouter:
    """Maps code-engineering intents to their registered FAZ 4 tool."""

    TOOL_BY_INTENT = {
        "REFACTOR": "Refactor",
        "DETECT_BUG": "BugDetector",
        "ANALYZE_PERFORMANCE": "Performance",
        "DETECT_DEAD_CODE": "DeadCode",
    }

    def route(self, command):
        tool = self.TOOL_BY_INTENT.get(command.intent)
        if tool is None:
            return None
        return {
            "tool": tool,
            "intent": command.intent,
            "risk": "MEDIUM" if tool != "DeadCode" else "LOW",
            "requires_review": True,
        }
