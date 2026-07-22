from Source.Core.Knowledge.script_knowledge import ScriptKnowledge

k = ScriptKnowledge()

print("=" * 60)

print(k.find_class("BallChainManager"))

print("=" * 60)

print(k.fields_of("BallChainManager"))

print("=" * 60)

print(k.methods_of("BallChainManager"))

print("=" * 60)

print(k.find_field("speed"))

print("=" * 60)

print(k.find_method("Update"))
