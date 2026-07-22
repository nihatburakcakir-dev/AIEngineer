from dataclasses import dataclass


@dataclass
class Action:
    action: str
    target: str
    location: str
    effect: str | None = None
    material: str | None = None
    color: str | None = None
