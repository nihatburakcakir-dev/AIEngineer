import unittest
from pathlib import Path
from types import SimpleNamespace

from Source.Core.Validator.unity_compile_validator import UnityCompileValidator


class UnityCompileValidatorTests(unittest.TestCase):
    def test_missing_unity_executable_returns_actionable_failure(self):
        config = SimpleNamespace(config={"unity_path": "Z:/missing/Unity.exe"})
        config.project_root = "C:/project"
        result = UnityCompileValidator(config).validate()

        self.assertFalse(result["valid"])
        self.assertIn("Unity executable not found", result["message"])


if __name__ == "__main__":
    unittest.main()
