class Step:

    def __init__(
        self,
        tool="",
        action="",
        parameters=None
    ):

        self.tool = tool

        self.action = action

        self.parameters = parameters or {}

    def __repr__(self):

        return (

            f"Step("

            f"tool='{self.tool}', "

            f"action='{self.action}')"

        )
