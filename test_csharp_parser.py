from Source.Core.Executor.file_executor import FileExecutor
from Source.Core.Executor.csharp_parser import CSharpParser

executor = FileExecutor()
parser = CSharpParser()

source = executor.read(
    r"Assets\Scripts\Managers\BallChainManager.cs"
)

field = parser.find_field(
    source,
    "speed"
)

print(field)
