from Source.Core.Tools.tool import Tool


class CompileTool(Tool):

    name = "Compile"

    def __init__(
        self,
        compiler
    ):

        self.compiler = compiler

    def execute(
        self,
        step
    ):

        return self.compiler.compile()
