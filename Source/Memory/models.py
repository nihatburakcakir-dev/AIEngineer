from dataclasses import asdict, dataclass, field


@dataclass
class LearnedLesson:
    code: str
    severity: str
    lesson: str
    alternative: str
    occurrences: int = 1
    example_prompts: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
from dataclasses import asdict, dataclass, field


@dataclass
class LearnedLesson:
    code: str
    severity: str
    lesson: str
    alternative: str
    occurrences: int = 1
    example_prompts: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
