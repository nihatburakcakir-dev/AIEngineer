class Intent:

    def __init__(
        self,
        name="",
        target="",
        action="",
        parameters=None,
        confidence=0.0,
        reasoning=""
    ):

        self.name = name
        self.target = target
        self.action = action
        self.parameters = parameters or {}
        self.confidence = confidence
        self.reasoning = reasoning

    def __repr__(self):

        return (
            f"Intent("
            f"name='{self.name}', "
            f"target='{self.target}', "
            f"action='{self.action}', "
            f"confidence={self.confidence})"
        )
