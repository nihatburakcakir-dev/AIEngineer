from Source.Core.Tools.tool import Tool


class PatchTool(Tool):

    name = "Patch"

    def __init__(
        self,
        patch_applier
    ):

        self.patch_applier = patch_applier

    def execute(
        self,
        step
    ):

        return self.patch_applier.apply(
            step.parameters
        )
