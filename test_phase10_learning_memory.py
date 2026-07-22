import json
import tempfile
import unittest
from pathlib import Path

from Source.Core.Executor.autonomous_executor import AutonomousExecutor, ExecutionStep
from Source.Core.Models.action_plan import ActionPlan
from Source.Core.Models.command import AICommand
from Source.Core.Planner.action_planner import ActionPlanner
from Source.Learning.Reflection.importer import LearningMemoryImporter
from Source.Memory.learning_memory import LearningMemory
from Source.Knowledge.unity_expertise import UnityExpertise


class LearningMemoryTests(unittest.TestCase):
    def _memory_with_events(self, directory):
        critique = Path(directory) / "critique.jsonl"
        events = [
            {"prompt": "Update Instantiate enemy", "warnings": [{"code": "per_frame_allocation", "severity": "HIGH", "rationale": "Frame allocation spikes.", "alternative": "Use an object pool."}]},
            {"prompt": "Every frame Instantiate projectile", "warnings": [{"code": "per_frame_allocation", "severity": "HIGH", "rationale": "Frame allocation spikes.", "alternative": "Use an object pool."}]},
        ]
        critique.write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")
        return LearningMemory(critique, Path(directory) / "memory.json", Path(directory) / "outcomes.jsonl", Path(directory) / "rules.json")

    def test_import_groups_repeated_critique_events_into_a_lesson(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = self._memory_with_events(directory)
            lessons = LearningMemoryImporter(memory).import_critique_events()
        lesson = next(item for item in lessons if item.code == "per_frame_allocation")
        self.assertEqual(lesson.occurrences, 2)
        self.assertIn("object pool", lesson.alternative)

    def test_new_plan_receives_similar_past_lesson_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = self._memory_with_events(directory)
            memory.import_critique_events()
            planner = ActionPlanner()
            planner.learning_memory = memory
            plan = planner.build(AICommand(intent="MODIFY_SCRIPT", prompt="Update Instantiate a projectile"))
        self.assertTrue(plan.context["learned_lessons"])
        self.assertTrue(any(item["code"] == "learned_per_frame_allocation" for item in plan.warnings))
        self.assertFalse(any(item["code"] == "learned_per_frame_component_lookup" for item in plan.warnings))

    def test_repeated_lesson_becomes_unity_expertise_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = self._memory_with_events(directory)
            memory.import_critique_events()
            expertise = UnityExpertise("C:/Bozkut1/Bozkurt", memory.rules_path)
            result = expertise.retrieve("Update Instantiate a projectile")
        self.assertTrue(any(item["topic"] == "learned" for item in result))

    def test_executor_records_success_and_failure_for_future_learning(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = LearningMemory(Path(directory) / "critique.jsonl", Path(directory) / "memory.json", Path(directory) / "outcomes.jsonl", Path(directory) / "rules.json")
            plan = ActionPlan(action="MODIFY_FIELD", target="Speed", context={"execution_authorized": True})
            result = AutonomousExecutor([lambda: True], learning_memory=memory).run_plan(plan, [ExecutionStep("MODIFY_FIELD", lambda: True)])
            outcome = json.loads(memory.outcomes_path.read_text(encoding="utf-8").strip())
        self.assertTrue(result.success)
        self.assertTrue(outcome["success"])
        self.assertEqual(outcome["resolution"], "Validation passed")


if __name__ == "__main__":
    unittest.main()
