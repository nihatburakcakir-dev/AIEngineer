from Source.Core.Pipeline.command_pipeline import CommandPipeline

p = CommandPipeline()

tests = [
    "Create Cube",
    "Topu büyüt",
    "Kurdun gözlerini kırmızı yap",
    "Create Prefab",
    "Generate Sprite",
    "Delete Ball"
]

for t in tests:
    print("="*50)
    print(t)
    print(p.process(t).to_dict())
