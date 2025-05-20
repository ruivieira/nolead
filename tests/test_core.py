"""Unit tests for the core functionality of nolead."""

import unittest
from typing import Optional

from nolead import Task, done, reset_pipeline, run_task, uses
from nolead.core import _TASKS


class TestNoLeadCore(unittest.TestCase):
    """Test cases for the core functionality of the nolead package."""

    def setUp(self) -> None:
        # Reset the pipeline before each test
        reset_pipeline()

        # Define test tasks
        @Task(name="test_task_1")
        def test_task_1() -> str:
            return "result_1"

        @Task(name="test_task_2")
        def test_task_2() -> Optional[str]:
            data = uses("test_task_1")
            return done(f"processed_{data}")

        @Task(name="test_task_3")
        def test_task_3() -> Optional[str]:
            data = uses("test_task_2")
            return done(f"final_{data}")

        self.test_tasks = {
            "test_task_1": test_task_1,
            "test_task_2": test_task_2,
            "test_task_3": test_task_3,
        }

    def test_task_registration(self) -> None:
        """Test that tasks are properly registered with the Task decorator."""
        task_name = "test_task_1"
        self.assertIn(task_name, _TASKS)
        self.assertEqual(_TASKS[task_name].name, task_name)

    def test_task_dependencies(self) -> None:
        """Test that dependencies are correctly set up."""
        # Run task_3 to establish dependencies
        _ = self.test_tasks["test_task_3"]()

        # Check dependencies
        self.assertIn("test_task_1", _TASKS["test_task_2"].dependencies)
        self.assertIn("test_task_2", _TASKS["test_task_3"].dependencies)

    def test_run_task(self) -> None:
        """Test running a task and getting its result."""
        result = run_task("test_task_3")
        self.assertEqual(result, "final_processed_result_1")

    def test_reset_pipeline(self) -> None:
        """Test that resetting the pipeline works correctly."""
        # Run a task
        run_task("test_task_2")

        # Run it again (should use cached result)
        run_task("test_task_2")

        # Reset pipeline
        reset_pipeline()

        # Run it again (should run fresh)
        result = run_task("test_task_2")
        self.assertEqual(result, "processed_result_1")


if __name__ == "__main__":
    unittest.main()
