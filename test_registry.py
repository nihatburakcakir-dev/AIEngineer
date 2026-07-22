from Source.Core.Tools.registry import ToolRegistry

from Source.Core.Tools.Builtin.backup_tool import BackupTool

from Source.Core.Backup.backup_manager import BackupManager

from Source.Brain.Models.step import Step


registry = ToolRegistry()

registry.register(

    BackupTool(BackupManager())

)

print()

print(registry.list())

tool = registry.get(

    "Backup"

)

step = Step(

    tool="Backup",

    action="create",

    parameters={

        "script":"BallChainManager"

    }

)

tool.execute(step)
