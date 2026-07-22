from Source.Core.Parser.command_parser import CommandParser
from Source.Core.Knowledge.script_knowledge import ScriptKnowledge
from Source.Core.Planner.target_resolver import TargetResolver

parser = CommandParser()
knowledge = ScriptKnowledge()
resolver = TargetResolver()

cmd = parser.parse("Topların hızını artır")

matches = knowledge.find_field("speed")

print(matches)

print()

print(resolver.resolve(cmd, matches))
