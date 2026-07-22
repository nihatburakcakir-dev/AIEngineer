import os
import shutil

from Source.Core.Config.config_manager import ConfigManager

class BackupManager:

    def __init__(self):

        self.config = ConfigManager()

    def create_backup(self, relative_path):

        source = os.path.join(
            self.config.project_root,
            relative_path
        )

        if not os.path.exists(source):

            return False

        backup = os.path.join(
            self.config.backup_folder,
            relative_path + ".bak"
        )

        os.makedirs(
            os.path.dirname(backup),
            exist_ok=True
        )

        shutil.copy2(
            source,
            backup
        )

        return True

    def restore_backup(self, relative_path):

        source = os.path.join(
            self.config.backup_folder,
            relative_path + ".bak"
        )

        if not os.path.exists(source):

            return False

        target = os.path.join(
            self.config.project_root,
            relative_path
        )

        os.makedirs(
            os.path.dirname(target),
            exist_ok=True
        )

        shutil.copy2(
            source,
            target
        )

        return True
