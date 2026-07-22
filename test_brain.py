from Source.Brain.orchestrator import Orchestrator
from Source.Core.Tools.registry import ToolRegistry
from Source.Core.Tools.Builtin.backup_tool import BackupTool
from Source.Core.Tools.Builtin.patch_tool import PatchTool
from Source.Core.Tools.Builtin.script_search_tool import ScriptSearchTool
from Source.Core.Tools.Builtin.validate_tool import ValidateTool
from Source.Core.Tools.Builtin.compile_tool import CompileTool
from Source.Core.Backup.backup_manager import BackupManager
from Source.Core.Executor.patch_applier import PatchApplier
from Source.Core.Knowledge.script_knowledge import ScriptKnowledge
from Source.Core.Validator.patch_validator import PatchValidator


class _NullCompiler:

    def compile(self):

        return True


registry = ToolRegistry()

registry.register(ScriptSearchTool(ScriptKnowledge()))
registry.register(BackupTool(BackupManager()))
registry.register(PatchTool(PatchApplier()))
registry.register(ValidateTool(PatchValidator()))
registry.register(CompileTool(_NullCompiler()))

brain = Orchestrator(registry)

commands = [

    "Topların hızını %20 artır.",

    "Speed'i 2 yap.",

    "Velocity değerini azalt.",

    "Yeni UI oluştur."

]

for command in commands:

    print()

    print("=" * 50)

    print("User")

    print(command)

    result = brain.execute(command)

    print()

    print("Success :", result.success)

    print("Message :", result.message)

    if "intent" in result.data:

        print("Intent  :", result.data["intent"])
