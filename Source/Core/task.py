from dataclasses import dataclass, field


@dataclass
class Task:
    id: str
    command: str
    steps: list[str] = field(default_factory=list)
    completed: bool = False
