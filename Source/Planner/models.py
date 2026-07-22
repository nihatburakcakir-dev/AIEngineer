from dataclasses import dataclass


@dataclass
class Task:

    action: str

    target: str = ""

    value: str = ""

    status: str = "pending"
