from Source.Core.Parser.command_parser import CommandParser
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Core.Patcher.patch_builder import PatchBuilder

parser = CommandParser()
planner = ActionPlanner()
builder = PatchBuilder()

cmd = parser.parse(
    "Topların hızını %20 artır"
)

plan = planner.build(cmd)

plan.operation = "multiply"
plan.value = 1.2

patch = builder.build(plan)

print(patch.to_dict())
