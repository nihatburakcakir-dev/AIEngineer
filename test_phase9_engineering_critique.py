import unittest
import tempfile
from pathlib import Path

from Source.Core.Critique.consent import ConsentParser
from Source.Core.Critique.critique_ledger import CritiqueLedger
from Source.Core.Critique.plan_critic import PlanCritic, UserDecision
from Source.Core.Executor.autonomous_executor import AutonomousExecutor, ExecutionStep
from Source.Core.Models.action_plan import ActionPlan
from Source.Core.Models.command import AICommand
from Source.Core.Planner.action_planner import ActionPlanner


class EngineeringCritiqueTests(unittest.TestCase):
    def test_per_frame_instantiation_gets_standard_warning_and_safe_alternative(self):
        command = AICommand(intent="MODIFY_SCRIPT", prompt="Update içinde her frame Instantiate ile yeni nesne oluştur")
        plan = ActionPlanner().build(command)
        warning = next(item for item in plan.warnings if item["code"] == "per_frame_allocation")
        self.assertEqual(warning["severity"], "HIGH")
        self.assertIn("object pool", warning["alternative"])
        self.assertTrue(plan.context["requires_informed_consent"])
        self.assertFalse(plan.context["execution_authorized"])

    def test_per_frame_component_lookup_gets_a_cache_alternative(self):
        command = AICommand(intent="MODIFY_SCRIPT", prompt="Update her frame GetComponent çağır")
        plan = ActionPlanner().build(command)
        warning = next(item for item in plan.warnings if item["code"] == "per_frame_component_lookup")
        self.assertIn("Cache", warning["alternative"])

    def test_user_can_make_an_informed_override(self):
        plan = ActionPlan(warnings=[{"requires_consent": True}])
        approved = PlanCritic.apply_decision(plan, UserDecision(True, "Benchmark scope requires this test."))
        self.assertTrue(approved.context["execution_authorized"])
        self.assertTrue(approved.context["user_decision"]["approved"])
        rejected = PlanCritic.apply_decision(ActionPlan(warnings=[{"requires_consent": True}]), UserDecision(False))
        self.assertFalse(rejected.context["execution_authorized"])

    def test_high_impact_refactor_requires_warning(self):
        command = AICommand(intent="REFACTOR", prompt="Refactor the project")
        plan = ActionPlanner().build(command)
        self.assertTrue(any(item["code"] == "high_impact_change" for item in plan.warnings))

    def test_phase4_performance_finding_is_added_when_a_selected_script_has_an_antipattern(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "BadUpdate.cs"
            script.write_text("void Update() { Instantiate(prefab); }", encoding="utf-8")
            command = AICommand(intent="MODIFY_SCRIPT", prompt="improve this script", scripts=[str(script)])
            plan = ActionPlanner().build(command)
        self.assertTrue(any(item["code"] == "faz4_performance_update_instantiate" for item in plan.warnings))

    def test_unity_expertise_rejects_a_pipeline_conflict(self):
        command = AICommand(intent="MODIFY_SCRIPT", prompt="create an HDRP material")
        plan = ActionPlanner().build(command)
        self.assertTrue(any(item["code"] == "unity_expertise_constraint" for item in plan.warnings))

    def test_natural_language_override_reaches_executor_authorization(self):
        plan = ActionPlanner().build(AICommand(intent="MODIFY_SCRIPT", prompt="Update every frame Instantiate object"))
        allowed = ConsentParser().apply_reply(plan, "Yine de uygula, benchmark için gerekli.")
        executor = AutonomousExecutor([lambda: True])
        result = executor.run_plan(allowed, [ExecutionStep("MODIFY_FIELD", lambda: True)])
        self.assertTrue(result.success)
        blocked = executor.run_plan(ActionPlanner().build(AICommand(intent="MODIFY_SCRIPT", prompt="Update every frame Instantiate object")), [ExecutionStep("MODIFY_FIELD", lambda: True)])
        self.assertFalse(blocked.success)
        self.assertIn("consent", blocked.perception.message.casefold())

    def test_ledger_creates_phase10_handoff_record(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = CritiqueLedger(Path(directory) / "critique.jsonl")
            command = AICommand(intent="MODIFY_SCRIPT", prompt="Update Instantiate")
            event = ledger.record(command, [{"code": "per_frame_allocation"}])
            contents = ledger.path.read_text(encoding="utf-8")
        self.assertEqual(event["memory_status"], "pending_phase_10_import")
        self.assertIn("per_frame_allocation", contents)


if __name__ == "__main__":
    unittest.main()
