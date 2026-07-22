import unittest

from Source.Core.Executor.autonomous_executor import AutonomousExecutor, ExecutionStep


class AutonomousExecutorTests(unittest.TestCase):
    def test_low_risk_plan_executes_and_validates(self):
        executed, backed_up = [], []
        runner = AutonomousExecutor(
            [lambda: {"valid": True, "message": "Compile passed"}],
            backup=lambda file: backed_up.append(file) is None,
        )
        result = runner.run([ExecutionStep("MODIFY_FIELD", lambda: executed.append("changed"), ["Assets/Player.cs"])])

        self.assertTrue(result.success)
        self.assertEqual(executed, ["changed"])
        self.assertEqual(backed_up, ["Assets/Player.cs"])

    def test_failure_is_replanned_then_succeeds(self):
        outcomes = iter([False, True])
        repairs = []
        runner = AutonomousExecutor([lambda: next(outcomes)], max_attempts=2)
        result = runner.run(
            [ExecutionStep("MODIFY_FIELD", lambda: None)],
            repair_planner=lambda perception, attempt: repairs.append(perception.message) or [ExecutionStep("MODIFY_FIELD", lambda: None)],
        )

        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(repairs, ["Validation failed"])

    def test_exhausted_retries_roll_back_and_high_risk_needs_approval(self):
        rolled_back = []
        runner = AutonomousExecutor(
            [lambda: False],
            backup=lambda _: True,
            rollback=lambda file: rolled_back.append(file) is None,
            max_attempts=2,
        )
        failed = runner.run([ExecutionStep("MODIFY_FIELD", lambda: None, ["Assets/Player.cs"])])
        blocked = runner.run([ExecutionStep("DELETE_FILE", lambda: None, ["Assets/Player.cs"], "HIGH")])

        self.assertFalse(failed.success)
        self.assertTrue(failed.rolled_back)
        self.assertEqual(rolled_back, ["Assets/Player.cs"])
        self.assertIn("Approval required", blocked.perception.message)

    def test_repair_steps_back_up_any_newly_touched_file(self):
        backed_up = []
        outcomes = iter([False, True])
        runner = AutonomousExecutor(
            [lambda: next(outcomes)],
            backup=lambda file: backed_up.append(file) is None,
            max_attempts=2,
        )
        result = runner.run(
            [ExecutionStep("MODIFY_FIELD", lambda: None, ["Assets/A.cs"])],
            repair_planner=lambda _perception, _attempt: [
                ExecutionStep("MODIFY_FIELD", lambda: None, ["Assets/B.cs"])
            ],
        )

        self.assertTrue(result.success)
        self.assertEqual(backed_up, ["Assets/A.cs", "Assets/B.cs"])


if __name__ == "__main__":
    unittest.main()
