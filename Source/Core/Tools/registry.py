class ToolRegistry:

    def __init__(self):

        self.tools = {}

    def register(
        self,
        tool
    ):

        self.tools[tool.name] = tool

    def get(
        self,
        name
    ):

        return self.tools.get(name)

    def exists(
        self,
        name
    ):

        return name in self.tools

    def list(self):

        return sorted(
            self.tools.keys()
        )
