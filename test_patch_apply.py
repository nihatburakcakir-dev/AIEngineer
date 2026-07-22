from Source.Core.Parser.command_parser import CommandParser
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Core.Patcher.patch_builder import PatchBuilder
from Source.Core.Executor.patch_applier import PatchApplier

parser = CommandParser()
planner = ActionPlanner()
builder = PatchBuilder()
executor = PatchApplier()

cmd = parser.parse(
    "Topların hızını %20 artır"
)

plan = planner.build(cmd)

plan.operation = "multiply"
plan.value = 1.2

patch = builder.build(plan)

print(executor.apply(patch))
