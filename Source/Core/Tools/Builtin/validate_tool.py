from Source.Core.Tools.tool import Tool


class ValidateTool(Tool):

    name = "Validate"

    def __init__(
        self,
        validator
    ):

        self.validator = validator

    def execute(
        self,
        step
    ):

        return self.validator.validate(
            step.parameters
        )
