from Source.Core.Parser.command_parser import CommandParser
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Core.Generator.code_generator import CodeGenerator

parser = CommandParser()
planner = ActionPlanner()
generator = CodeGenerator()

cmd = parser.parse("Topların hızını artır")

plan = planner.build(cmd)

plan.operation = "multiply"
plan.value = 1.2

result = generator.generate(plan)

print(result)
