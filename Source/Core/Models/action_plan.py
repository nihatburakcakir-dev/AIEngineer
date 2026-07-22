from dataclasses import dataclass, field

@dataclass
class ActionPlan:

    action: str = ""

    target: str = ""

    target_class: str = ""

    target_field: str = ""

    target_method: str = ""

    value = None

    operation: str = ""

    confidence: float = 0.0

    risk: str = "MEDIUM"

    steps: list = field(default_factory=list)

    warnings: list = field(default_factory=list)

    context: dict = field(default_factory=dict)

    def to_dict(self):

        return {
            "action": self.action,
            "target": self.target,
            "target_class": self.target_class,
            "target_field": self.target_field,
            "target_method": self.target_method,
            "value": self.value,
            "operation": self.operation,
            "confidence": self.confidence,
            "risk": self.risk,
            "steps": self.steps,
            "warnings": self.warnings,
            "context": self.context
        }
