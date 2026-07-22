from Source.Core.Tools.tool import Tool


class ScriptSearchTool(Tool):

    name = "ScriptSearch"

    def __init__(
        self,
        script_knowledge
    ):

        self.script_knowledge = script_knowledge

    def execute(
        self,
        step
    ):

        script = step.parameters.get(
            "script"
        )

        result = self.script_knowledge.find_script(
            script
        )

        if result is None:

            return False

        step.parameters["path"] = result

        return True
