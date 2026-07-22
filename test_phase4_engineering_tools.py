import tempfile
import unittest
from pathlib import Path

from Source.Core.Tools.Builtin.bug_detector_tool import BugDetectorTool
from Source.Core.Tools.Builtin.performance_tool import PerformanceTool
from Source.Core.Tools.Builtin.refactor_tool import RefactorTool
from Source.Core.Tools.engineering_registry import register_engineering_tools
from Source.Core.Tools.registry import ToolRegistry
from Source.Core.Tools.Builtin.dead_code_tool import DeadCodeTool
from Source.Core.Knowledge.project_graph import ProjectGraph
from Source.Core.Pipeline.command_pipeline import CommandPipeline
from Source.Core.Bootstrap.bootstrap import Bootstrap


class EngineeringToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.script = Path(self.temp_dir.name) / "Example.cs"
        self.script.write_text("""using UnityEngine;
public class Example : MonoBehaviour {
    private Rigidbody body;
    // body should stay body in a comment
    void Update() { GetComponent<Rigidbody>(); Instantiate(gameObject); var label = "a" + "b"; }
    void Loop() { while (true) { } }
}""", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bug_and_performance_tools_report_unity_antipatterns(self):
        bugs = BugDetectorTool().analyze(self.script)
        performance = PerformanceTool().analyze(self.script)

        self.assertIn("infinite_loop", [item["rule"] for item in bugs])
        self.assertIn("update_get_component", [item["rule"] for item in performance])
        self.assertIn("update_instantiate", [item["rule"] for item in performance])
        self.assertIn("replace_with_object_pool", [item["operation"] for item in PerformanceTool().propose_fixes(self.script)])

    def test_refactor_preview_is_identifier_safe_and_does_not_write(self):
        result = RefactorTool().rename_symbol(self.script, "body", "rigidbody", apply=False)

        self.assertEqual(result["occurrences"], 1)
        self.assertFalse(result["applied"])
        self.assertIn("rigidbody", result["preview"])
        self.assertIn("body", self.script.read_text(encoding="utf-8"))
        self.assertIn("body should stay body", result["preview"])

    def test_refactor_detects_duplicates_and_plans_method_extraction(self):
        self.script.write_text("""class Example {
    void First() { Debug.Log(1); }
    void Second() { Debug.Log(1); }
}""", encoding="utf-8")
        tool = RefactorTool()

        duplicates = tool.find_duplicate_methods(self.script)
        plan = tool.extract_method_plan(self.script, 2, 2, "LogOnce")

        self.assertEqual(duplicates[0]["methods"], ["First", "Second"])
        self.assertEqual(plan["operation"], "extract_method")
        self.assertTrue(plan["requires_review"])

    def test_extract_method_can_apply_a_reviewed_patch(self):
        self.script.write_text("""class Example {
    void Update() {
        Debug.Log(1);
    }
}""", encoding="utf-8")

        result = RefactorTool().extract_method_plan(self.script, 3, 3, "LogOnce", apply=True)
        updated = self.script.read_text(encoding="utf-8")

        self.assertTrue(result["applied"])
        self.assertIn("LogOnce();", updated)
        self.assertIn("private void LogOnce()", updated)

    def test_engineering_tools_are_registered(self):
        registry = register_engineering_tools(ToolRegistry())

        self.assertEqual(registry.list(), ["BugDetector", "DeadCode", "Performance", "Refactor"])

    def test_dead_code_tool_reports_only_unreferenced_scripts(self):
        graph = ProjectGraph(str(Path(self.temp_dir.name) / "graph.db"))
        graph.cur.executemany(
            "INSERT INTO project_graph_nodes(path, asset_type) VALUES (?, ?)",
            [("Assets/Scene.unity", "Scene"), ("Assets/Used.cs", "Script"), ("Assets/Unused.cs", "Script")],
        )
        graph.cur.execute(
            "INSERT INTO project_graph_edges(source_path, target_path, relation) VALUES (?, ?, ?)",
            ("Assets/Scene.unity", "Assets/Used.cs", "references"),
        )
        graph.conn.commit()

        findings = DeadCodeTool().find_unreferenced_scripts(graph, self.temp_dir.name)
        graph.close()

        self.assertEqual(findings, [{"path": "Assets/Unused.cs", "reason": "No Unity asset graph reference found; inspect before deletion."}])

    def test_engineering_commands_select_the_correct_registered_tool(self):
        pipeline = CommandPipeline()

        performance = pipeline.process("bu scripti performans acisindan incele")
        bug = pipeline.process("bu scriptte bug bul")

        self.assertEqual(performance.metadata["engineering_route"]["tool"], "Performance")
        self.assertEqual(bug.metadata["engineering_route"]["tool"], "BugDetector")

    def test_bootstrap_registers_engineering_tools_and_dead_method_candidates(self):
        self.script.write_text("""class Example {
    void Awake() { }
    void Unused() { }
}""", encoding="utf-8")

        registry = Bootstrap().build().executor.registry
        methods = DeadCodeTool().find_unreferenced_methods(self.script)

        self.assertTrue(registry.exists("Refactor"))
        self.assertEqual(methods[0]["method"], "Unused")


if __name__ == "__main__":
    unittest.main()
