from Source.Analysis.script_indexer import ScriptIndexer

idx = ScriptIndexer(r"C:\Bozkut1\Bozkurt")

scripts = idx.scan()

print("Scripts:", len(scripts))
print("=" * 60)

for s in scripts[:10]:
    print(s["name"])
    print(" Fields :", len(s["fields"]))
    print(" Methods:", len(s["methods"]))
    print()
