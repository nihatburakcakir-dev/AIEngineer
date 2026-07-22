import shutil
import os

from Source.Core.Config.config_manager import ConfigManager

class RollbackManager:

    def __init__(self):

        self.config = ConfigManager()

    def rollback(self, relative_path):

        project_file = os.path.join(
            self.config.project_root,
            relative_path
        )

        backup_file = os.path.join(
            self.config.backup_folder,
            relative_path + ".bak"
        )

        if not os.path.exists(backup_file):

            return False

        os.makedirs(
            os.path.dirname(project_file),
            exist_ok=True
        )

        shutil.copy2(
            backup_file,
            project_file
        )

        return True
