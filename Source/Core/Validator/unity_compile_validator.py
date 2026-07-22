"""Unity batch-mode compiler validator used after autonomous changes."""

import subprocess
from pathlib import Path

from Source.Core.Config.config_manager import ConfigManager


class UnityCompileValidator:
    def __init__(self, config=None, timeout_seconds=300):
        self.config = config or ConfigManager()
        self.timeout_seconds = timeout_seconds

    def validate(self):
        unity_path = Path(self.config.config["unity_path"])
        if not unity_path.is_file():
            return {"valid": False, "message": f"Unity executable not found: {unity_path}"}
        try:
            completed = subprocess.run(
                [str(unity_path), "-batchmode", "-quit", "-projectPath", self.config.project_root],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return {"valid": False, "message": "Unity compilation timed out."}
        output = f"{completed.stdout}\n{completed.stderr}"
        failed = completed.returncode != 0 or "error CS" in output or "error " in output.lower()
        return {"valid": not failed, "message": "Unity compilation passed." if not failed else output[-4000:]}
