from Source.Core.Tools.tool import Tool


class BackupTool(Tool):

    name = "Backup"

    def __init__(
        self,
        backup_manager
    ):

        self.backup_manager = backup_manager

    def execute(
        self,
        step
    ):

        script = step.parameters.get(
            "script"
        )

        if not script:

            return False

        return self.backup_manager.create_backup(
            script
        )
