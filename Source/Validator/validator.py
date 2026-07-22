from Source.Executor.executor import Command


class Validator:

    ACTIONS = {

        "FindObject",

        "FindPrefab",

        "Instantiate",

        "SetParent",

        "ResetTransform",

        "Destroy",

        "Select",

        "Move",

        "Rotate",

        "Scale",

        "ChangeColor"

    }


    def validate(self, command: Command, context: dict) -> Command:

        if command.action not in self.ACTIONS:

            raise ValueError(
                f"Unknown action '{command.action}'"
            )

        objects = context.get(
            "objects",
            []
        )

        if command.action == "FindObject":

            names = [
                obj["name"]
                for obj in objects
            ]

            if command.target not in names:

                raise ValueError(
                    f"Target '{command.target}' not found."
                )

        return command
