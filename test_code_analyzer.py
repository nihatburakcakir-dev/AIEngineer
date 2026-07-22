from Source.Analysis.code_analyzer import CodeAnalyzer

a = CodeAnalyzer(r"C:\Bozkut1\Bozkurt")

info = a.analyze(
    r"Assets\Scripts\Managers\BallChainManager.cs"
)

for k, v in info.items():
    print(k)
    print(v)
    print()
