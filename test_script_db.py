from Source.Analysis.script_indexer import ScriptIndexer
from Source.Analysis.script_database import ScriptDatabase
from Source.Analysis.code_analyzer import CodeAnalyzer

PROJECT = r"C:\Bozkut1\Bozkurt"

idx = ScriptIndexer(PROJECT)

analyzer = CodeAnalyzer(PROJECT)

db = ScriptDatabase()

db.clear()

for script in idx.scan():

    analysis = analyzer.analyze(
        script["path"]
    )

    db.insert(
        script,
        analysis
    )

print("Indexed:", db.count())
