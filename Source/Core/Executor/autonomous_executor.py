"""Bounded autonomous plan -> apply -> validate -> repair execution loop."""

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


LOW_RISK_ACTIONS = {"MODIFY_FIELD", "CHANGE_COLOR", "CREATE_OBJECT"}
HIGH_RISK_ACTIONS = {"DELETE_OBJECT", "DELETE_FILE", "REFACTOR"}


@dataclass
class ExecutionStep:
    action: str
    execute: Callable[[], Any]
    files: list[str] = field(default_factory=list)
    risk: str = "LOW"


@dataclass
class PerceptionResult:
    passed: bool
    message: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class AutonomousResult:
    success: bool
    attempts: int
    perception: PerceptionResult
    rolled_back: bool = False
    history: list[dict] = field(default_factory=list)


class AutonomousExecutor:
    """Executes a plan safely, with bounded repair attempts and rollback."""

    def __init__(
        self,
        validators: Iterable[Callable[[], Any]],
        backup: Callable[[str], bool] | None = None,
        rollback: Callable[[str], bool] | None = None,
        max_attempts: int = 3,
        learning_memory=None,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.validators = list(validators)
        self.backup = backup
        self.rollback = rollback
        self.max_attempts = max_attempts
        self.learning_memory = learning_memory

    @staticmethod
    def risk_for(action: str) -> str:
        if action in HIGH_RISK_ACTIONS:
            return "HIGH"
        if action in LOW_RISK_ACTIONS:
            return "LOW"
        return "MEDIUM"

    def run(
        self,
        steps: list[ExecutionStep],
        repair_planner: Callable[[PerceptionResult, int], list[ExecutionStep]] | None = None,
        approval_granted: bool = False,
    ) -> AutonomousResult:
        if not steps:
            perception = PerceptionResult(False, "Plan contains no executable steps.")
            return AutonomousResult(False, 0, perception)

        original_files = sorted({file for step in steps for file in step.files})
        for step in steps:
            risk = step.risk or self.risk_for(step.action)
            if risk == "HIGH" and not approval_granted:
                perception = PerceptionResult(False, f"Approval required for high-risk action: {step.action}")
                return AutonomousResult(False, 0, perception)

        if self.backup:
            for file in original_files:
                if not self.backup(file):
                    perception = PerceptionResult(False, f"Backup failed: {file}")
                    return AutonomousResult(False, 0, perception)

        active_steps = steps
        history = []
        for attempt in range(1, self.max_attempts + 1):
            try:
                execution_results = [step.execute() for step in active_steps]
                if any(result is False for result in execution_results):
                    perception = PerceptionResult(False, "One or more plan steps could not be applied.")
                else:
                    perception = self._validate()
            except Exception as error:
                perception = PerceptionResult(False, f"Execution error: {error}")

            history.append({"attempt": attempt, "steps": len(active_steps), "perception": perception.message})
            if perception.passed:
                return AutonomousResult(True, attempt, perception, history=history)

            if repair_planner and attempt < self.max_attempts:
                active_steps = repair_planner(perception, attempt)
                if active_steps:
                    repair_files = {file for step in active_steps for file in step.files}
                    new_files = sorted(repair_files - set(original_files))
                    backup_failed = False
                    if self.backup:
                        for file in new_files:
                            if not self.backup(file):
                                perception = PerceptionResult(False, f"Backup failed: {file}")
                                backup_failed = True
                                break
                    if backup_failed:
                        break
                    original_files.extend(new_files)
                    continue
            break

        rolled_back = False
        if self.rollback:
            rolled_back = all(self.rollback(file) for file in original_files)
        return AutonomousResult(False, len(history), perception, rolled_back, history)

    def run_plan(
        self,
        plan,
        steps: list[ExecutionStep],
        repair_planner: Callable[[PerceptionResult, int], list[ExecutionStep]] | None = None,
    ) -> AutonomousResult:
        """Execute only when the critiqued plan has user authorization where required."""
        if plan.context.get("requires_informed_consent") and not plan.context.get("execution_authorized"):
            perception = PerceptionResult(False, "Informed user consent is required before this critiqued plan can execute.")
            return AutonomousResult(False, 0, perception)
        result = self.run(steps, repair_planner=repair_planner, approval_granted=bool(plan.context.get("execution_authorized")))
        if self.learning_memory is not None:
            self.learning_memory.record_execution(plan, result)
        return result

    def _validate(self) -> PerceptionResult:
        messages, details = [], {}
        for index, validator in enumerate(self.validators):
            result = validator()
            if isinstance(result, PerceptionResult):
                normalized = result
            elif isinstance(result, dict):
                normalized = PerceptionResult(bool(result.get("valid", result.get("passed", False))), result.get("message", ""), result)
            else:
                normalized = PerceptionResult(bool(result), "Validation passed" if result else "Validation failed")
            messages.append(normalized.message)
            details[f"validator_{index}"] = normalized.details
            if not normalized.passed:
                return PerceptionResult(False, normalized.message or "Validation failed", details)
        return PerceptionResult(True, "; ".join(message for message in messages if message) or "All validations passed", details)
