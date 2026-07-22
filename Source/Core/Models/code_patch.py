from dataclasses import dataclass, field

@dataclass
class CodePatch:

    file: str = ""

    action: str = ""

    target: str = ""

    value = None

    operation: str = ""

    description: str = ""

    metadata: dict = field(default_factory=dict)

    def to_dict(self):

        return {
            "file": self.file,
            "action": self.action,
            "target": self.target,
            "value": self.value,
            "operation": self.operation,
            "description": self.description,
            "metadata": self.metadata
        }
