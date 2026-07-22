class BrainResult:

    def __init__(
        self,
        success=False,
        message="",
        data=None
    ):

        self.success = success
        self.message = message
        self.data = data or {}

    def __repr__(self):

        return (
            f"BrainResult("
            f"success={self.success}, "
            f"message='{self.message}')"
        )
