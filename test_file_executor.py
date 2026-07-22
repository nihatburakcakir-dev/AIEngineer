from Source.Core.Executor.file_executor import FileExecutor

executor = FileExecutor()

relative = r"Assets\Scripts\Managers\BallChainManager.cs"

print("Exists :", executor.exists(relative))

text = executor.read(relative)

print()

print(text[:500])
