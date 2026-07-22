"""Regression coverage for FAZ 1's C# code-understanding model."""

import tempfile
import unittest
from pathlib import Path

from Source.Core.CodeModel.parser import CodeParser


class CodeModelTests(unittest.TestCase):
    def parse(self, source):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Example.cs"
            path.write_text(source, encoding="utf-8")
            return CodeParser().parse(path)

    def test_parser_keeps_members_in_their_own_class_scope(self):
        model = self.parse("""public class PlayerController : MonoBehaviour, IDamageable {
    [SerializeField] private int health = 100;
    public string DisplayName { get; private set; }
    void Update() { var localOnly = 1; }
    public void Damage(int amount, string reason) { }
}
public class Helper { public float Speed; }""")

        self.assertEqual([cls.name for cls in model.classes], ["PlayerController", "Helper"])
        player, helper = model.classes
        self.assertEqual(player.base_class, "MonoBehaviour")
        self.assertEqual([(field.name, field.value) for field in player.fields], [("health", "100")])
        self.assertEqual([(prop.name, prop.type) for prop in player.properties], [("DisplayName", "string")])
        self.assertEqual([method.name for method in player.methods], ["Update", "Damage"])
        self.assertEqual(player.methods[1].parameters, ["int amount", "string reason"])
        self.assertEqual([(field.name, field.type) for field in helper.fields], [("Speed", "float")])

    def test_parser_ignores_declarations_in_comments_and_strings(self):
        model = self.parse("""class Example {
    // public int Fake;
    private string message = "class NotAClass { public int Fake; }";
    /* public void FakeMethod() {} */
    public bool IsReady() { return true; }
}""")

        cls = model.classes[0]
        self.assertEqual([field.name for field in cls.fields], ["message"])
        self.assertEqual([method.name for method in cls.methods], ["IsReady"])


if __name__ == "__main__":
    unittest.main()
