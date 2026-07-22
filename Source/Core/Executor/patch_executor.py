import re

from Source.Core.Config.config_manager import ConfigManager

class PatchExecutor:

    def __init__(self):

        self.config = ConfigManager()

    def load_file(self, relative_path):

        full_path = self.config.project_root + "/" + relative_path.replace("\\", "/")

        with open(
            full_path,
            encoding="utf8"
        ) as f:

            return f.read()

    def find_field(self, source, field):

        pattern = rf"\b{field}\b"

        return re.search(
            pattern,
            source
        ) is not None

    def execute(self, patch):

        source = self.load_file(
            patch.file
        )

        exists = self.find_field(
            source,
            patch.target
        )

        return {
            "file": patch.file,
            "field": patch.target,
            "found": exists
        }
