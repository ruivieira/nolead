"""Test cases for parallel task execution functionality."""

import time
import unittest
from typing import Any, Dict

from nolead import Task, parallel, reset_pipeline, run_task, uses


class TestParallelExecution(unittest.TestCase):
    """Test cases for parallel task execution."""

    def setUp(self) -> None:
        """Reset the pipeline before each test."""
        reset_pipeline()

    def test_parallel_execution(self) -> None:
        """Test that tasks execute in parallel and results are correctly merged."""

        # Define test tasks
        @Task()
        def task1() -> Dict[str, int]:
            return {"value": 1}

        @Task()
        def task2() -> Dict[str, int]:
            return {"value": 2}

        @Task()
        def task3() -> Dict[str, int]:
            return {"value": 3}

        @Task()
        def combined_task() -> Dict[str, bool]:
            results = parallel([task1, task2, task3])
            # Results should be a dictionary with task names as keys
            self.assertIn("task1", results)
            self.assertIn("task2", results)
            self.assertIn("task3", results)
            # Each task result should be the dictionary returned by the task
            self.assertEqual(results["task1"]["value"], 1)
            self.assertEqual(results["task2"]["value"], 2)
            self.assertEqual(results["task3"]["value"], 3)
            return {"success": True}

        result = run_task(combined_task)
        self.assertTrue(result["success"])

    def test_parallel_execution_with_dependencies(self) -> None:
        """Test that parallel tasks share common dependencies correctly."""

        @Task()
        def common_dependency() -> Dict[str, list]:
            return {"data": [1, 2, 3, 4, 5]}

        @Task()
        def process1() -> Dict[str, int]:
            data = uses(common_dependency)
            return {"sum": sum(data["data"])}

        @Task()
        def process2() -> Dict[str, int]:
            _ = uses(common_dependency)
            return {"product": 1}  # Initialize product

        @Task()
        def final_task() -> Dict[str, int]:
            results = parallel([process1, process2])
            return {
                "sum": results["process1"]["sum"],
                "product": results["process2"]["product"],
            }

        result = run_task(final_task)
        self.assertEqual(result["sum"], 15)  # 1+2+3+4+5 = 15
        self.assertEqual(result["product"], 1)

    def test_parallel_performance(self) -> None:
        """Test that parallel execution is faster than sequential execution."""

        # Create tasks that have significant execution time
        @Task()
        def slow_task1() -> Dict[str, int]:
            time.sleep(0.1)
            return {"result": 1}

        @Task()
        def slow_task2() -> Dict[str, int]:
            time.sleep(0.1)
            return {"result": 2}

        @Task()
        def slow_task3() -> Dict[str, int]:
            time.sleep(0.1)
            return {"result": 3}

        # Define a task that runs the slow tasks in parallel
        @Task()
        def parallel_execution() -> Dict[str, Any]:
            start_time = time.time()
            results = parallel([slow_task1, slow_task2, slow_task3])
            parallel_time = time.time() - start_time
            return {"time": parallel_time, "results": results}

        # Define a task that runs the slow tasks sequentially
        @Task()
        def sequential_execution() -> Dict[str, Any]:
            start_time = time.time()
            result1 = uses(slow_task1)
            result2 = uses(slow_task2)
            result3 = uses(slow_task3)
            sequential_time = time.time() - start_time
            return {
                "time": sequential_time,
                "results": {
                    "slow_task1": result1,
                    "slow_task2": result2,
                    "slow_task3": result3,
                },
            }

        # Run both tasks and compare execution times
        parallel_result = run_task(parallel_execution)
        reset_pipeline()  # Reset pipeline state between runs
        sequential_result = run_task(sequential_execution)

        # Parallel execution should be faster (accounting for some overhead)
        self.assertLess(parallel_result["time"], sequential_result["time"])

        # Both approaches should return the same results
        self.assertEqual(
            parallel_result["results"]["slow_task1"]["result"],
            sequential_result["results"]["slow_task1"]["result"],
        )
        self.assertEqual(
            parallel_result["results"]["slow_task2"]["result"],
            sequential_result["results"]["slow_task2"]["result"],
        )
        self.assertEqual(
            parallel_result["results"]["slow_task3"]["result"],
            sequential_result["results"]["slow_task3"]["result"],
        )


if __name__ == "__main__":
    unittest.main()
