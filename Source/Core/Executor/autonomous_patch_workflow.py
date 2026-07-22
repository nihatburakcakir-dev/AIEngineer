"""Production adapter connecting patching, validation, backup and rollback."""

from Source.Core.Backup.backup_manager import BackupManager
from Source.Core.Executor.autonomous_executor import AutonomousExecutor, ExecutionStep
from Source.Core.Executor.patch_applier import PatchApplier
from Source.Core.Rollback.rollback_manager import RollbackManager
from Source.Core.Validator.patch_validator import PatchValidator


class AutonomousPatchWorkflow:
    def __init__(self, compile_validator=None):
        self.applier = PatchApplier()
        self.validator = PatchValidator()
        self.backup = BackupManager()
        self.rollback = RollbackManager()
        self.compile_validator = compile_validator

    def run(self, patch, repair_planner=None, approval_granted=False):
        validators = [lambda: self.validator.validate(patch)]
        if self.compile_validator:
            validators.append(self.compile_validator)
        executor = AutonomousExecutor(
            validators=validators,
            backup=self.backup.create_backup,
            rollback=self.rollback.rollback,
        )
        step = ExecutionStep(
            action=patch.action,
            execute=lambda: self.applier.apply(patch),
            files=[patch.file],
            risk=AutonomousExecutor.risk_for(patch.action),
        )
        return executor.run([step], repair_planner, approval_granted)
