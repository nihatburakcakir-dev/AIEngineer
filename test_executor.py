from Source.Core.Parser.command_parser import CommandParser
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Core.Patcher.patch_builder import PatchBuilder
from Source.Core.Executor.patch_executor import PatchExecutor

parser = CommandParser()
planner = ActionPlanner()
builder = PatchBuilder()
executor = PatchExecutor()

cmd = parser.parse(
    "Topların hızını artır"
)

plan = planner.build(cmd)

plan.operation = "multiply"
plan.value = 1.2

patch = builder.build(plan)

result = executor.execute(
    patch
)

print(result)
