from Source.Executor.executor import Command


class Validator:

    ACTION_MAP = {
        "add": "ADD_EFFECT",
        "add effect": "ADD_EFFECT",
        "add_effect": "ADD_EFFECT",
        "addeffect": "ADD_EFFECT",

        "select": "SELECT_OBJECT",
        "select object": "SELECT_OBJECT",
        "select_object": "SELECT_OBJECT",

        "move": "MOVE_OBJECT",
        "move object": "MOVE_OBJECT",
        "move_object": "MOVE_OBJECT",

        "change color": "CHANGE_COLOR",
        "change_color": "CHANGE_COLOR",

        "create": "CREATE_OBJECT",
        "create object": "CREATE_OBJECT",
        "create_object": "CREATE_OBJECT"
    }

    def validate(self, command: Command, context: dict) -> Command:

        objects = context.get("objects", [])

        names = [
            obj.get("name", "")
            for obj in objects
        ]

        if command.target not in names:
            raise ValueError(
                f"Target '{command.target}' not found."
            )

        key = (
            command.action
            .strip()
            .lower()
            .replace("-", " ")
        )

        while "  " in key:
            key = key.replace("  ", " ")

        if key not in self.ACTION_MAP:
            raise ValueError(
                f"Unknown action '{command.action}'"
            )

        command.action = self.ACTION_MAP[key]

        return command
