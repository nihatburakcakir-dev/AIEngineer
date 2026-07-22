from Source.Core.Backup.backup_manager import BackupManager
from Source.Core.Executor.patch_applier import PatchApplier
from Source.Core.Rollback.rollback_manager import RollbackManager
from Source.Core.Parser.command_parser import CommandParser
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Core.Patcher.patch_builder import PatchBuilder

relative = r"Assets\Scripts\Managers\BallChainManager.cs"

backup = BackupManager()

print("Backup :", backup.create_backup(relative))

parser = CommandParser()
planner = ActionPlanner()
builder = PatchBuilder()
applier = PatchApplier()

cmd = parser.parse(
    "Topların hızını artır"
)

plan = planner.build(cmd)
plan.operation = "multiply"
plan.value = 1.2

patch = builder.build(plan)

print("Patch :", applier.apply(patch))

rollback = RollbackManager()

print("Rollback :", rollback.rollback(relative))
