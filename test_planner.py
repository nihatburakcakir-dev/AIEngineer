from Source.Core.Parser.command_parser import CommandParser
from Source.Core.Planner.action_planner import ActionPlanner

parser = CommandParser()
planner = ActionPlanner()

cmd = parser.parse(
    "Topların hızını artır"
)

plan = planner.build(cmd)

print(plan.to_dict())
