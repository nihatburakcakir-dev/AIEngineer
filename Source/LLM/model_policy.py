"""Explicit local-first routing policy for Phase 8 model tasks."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TaskModelPolicy:
    task: str
    model: str
    execution: str
    cloud_fallback: str
    rationale: str

    def to_dict(self):
        return asdict(self)


class ModelPolicy:
    """Keeps cloud use opt-in and makes every routing choice reviewable."""

    LOCAL_TASKS = {
        "chat": "Short interactive responses are reliable with the local text model.",
        "planning": "Structured planning stays private and works without internet access.",
        "code_generation": "Small code changes are generated locally, then validated by the existing executor.",
        "vision": "Screenshot analysis uses the installed local multimodal model, but only strict ImageParser output may reach generation; uncertain output is rejected for review or a local-model upgrade.",
    }

    def __init__(self, config):
        self.config = config

    def for_task(self, task: str) -> TaskModelPolicy:
        if task not in self.LOCAL_TASKS:
            raise ValueError(f"No local model policy is defined for task '{task}'.")
        return TaskModelPolicy(
            task=task,
            model=self.config.model_for(task),
            execution="local",
            cloud_fallback="explicitly-configured-only" if getattr(self.config, "cloud_optional", False) else "disabled",
            rationale=self.LOCAL_TASKS[task],
        )

    def all(self):
        return [self.for_task(task) for task in self.LOCAL_TASKS]
