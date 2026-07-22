from Source.Analysis.project_indexer import ProjectIndexer

idx = ProjectIndexer(r"C:\Bozkut1\Bozkurt")

result = idx.scan()

print("=" * 50)

for category, files in result.items():
    print(f"{category:12}: {len(files)}")

print("=" * 50)

for category, files in result.items():
    if files:
        print(f"\n[{category}]")
        for f in files[:10]:
            print(" -", f)
