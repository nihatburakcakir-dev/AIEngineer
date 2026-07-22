import os

from Source.Core.Config.config_manager import ConfigManager

class FileExecutor:

    def __init__(self):

        self.config = ConfigManager()

    def get_full_path(self, relative_path):

        return os.path.normpath(
            os.path.join(
                self.config.project_root,
                relative_path
            )
        )

    def exists(self, relative_path):

        return os.path.exists(
            self.get_full_path(relative_path)
        )

    def read(self, relative_path):

        full_path = self.get_full_path(
            relative_path
        )

        with open(
            full_path,
            "r",
            encoding="utf-8"
        ) as f:

            return f.read()

    def write(self, relative_path, content):

        full_path = self.get_full_path(
            relative_path
        )

        with open(
            full_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)

        return True
