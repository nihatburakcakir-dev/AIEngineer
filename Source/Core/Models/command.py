from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class AICommand:
    intent: str = ""
    target: str = ""
    action: str = ""
    prompt: str = ""
    engine: str = "Unity"
    project: str = ""
    scene: str = ""
    assets: List[str] = field(default_factory=list)
    scripts: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "intent": self.intent,
            "target": self.target,
            "action": self.action,
            "prompt": self.prompt,
            "engine": self.engine,
            "project": self.project,
            "scene": self.scene,
            "assets": self.assets,
            "scripts": self.scripts,
            "parameters": self.parameters,
            "metadata": self.metadata
        }
