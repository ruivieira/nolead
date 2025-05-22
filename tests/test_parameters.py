"""Unit tests for parameter passing in nolead."""

import unittest
from typing import Any, Dict, List, Optional

from nolead import Task, reset_pipeline, run_task, uses


class TestParameterPassing(unittest.TestCase):
    """Test cases for parameter passing functionality in nolead."""

    def setUp(self) -> None:
        """Set up test tasks before each test."""
        # Reset the pipeline before each test
        reset_pipeline()

        # Define test tasks with parameters
        @Task(name="data_source")
        def data_source(count: int = 3, prefix: str = "item") -> List[Dict[str, Any]]:
            """Generate test data with configurable parameters."""
            return [{"id": i, "name": f"{prefix}_{i}"} for i in range(1, count + 1)]

        @Task(name="data_processor")
        def data_processor(multiplier: int = 2, count: int = 3) -> List[Dict[str, Any]]:
            """Process data with a configurable multiplier."""
            data = uses("data_source", count=count)
            result = [
                {**item, "value": item["id"] * multiplier} for item in data
            ]
            return result

        @Task(name="data_aggregator")
        def data_aggregator(op: str = "sum") -> Optional[int]:
            """Aggregate data with a configurable operation."""
            data = uses("data_processor")
            if op == "sum":
                return int(sum(item["value"] for item in data))
            elif op == "max":
                return int(max(item["value"] for item in data))
            return None

        self.test_tasks = {
            "data_source": data_source,
            "data_processor": data_processor,
            "data_aggregator": data_aggregator,
        }

    def test_default_parameters(self) -> None:
        """Test running tasks with default parameters."""
        result = run_task("data_aggregator")
        # Default: 3 items with multiplier 2, sum operation
        # (1*2) + (2*2) + (3*2) = 12
        self.assertEqual(result, 12)

    def test_override_parameters_in_run_task(self) -> None:
        """Test overriding parameters when calling run_task."""
        result = run_task("data_aggregator", op="max")
        # Default source and processor, but max operation
        # max(1*2, 2*2, 3*2) = 6
        self.assertEqual(result, 6)

    def test_override_parameters_in_dependency(self) -> None:
        """Test overriding parameters when calling uses function."""
        @Task(name="custom_aggregator")
        def custom_aggregator() -> int:
            # Override processor's multiplier parameter
            data = uses("data_processor", multiplier=10)
            return sum(item["value"] for item in data)

        result = run_task("custom_aggregator")
        # Default source (3 items), multiplier 10
        # (1*10) + (2*10) + (3*10) = 60
        self.assertEqual(result, 60)

    def test_parameter_chain(self) -> None:
        """Test passing parameters through a chain of tasks."""
        @Task(name="custom_chain")
        def custom_chain() -> int:
            # Override source parameters
            data = uses("data_processor", multiplier=3)
            return sum(item["value"] for item in data)

        # First run with defaults
        result1 = run_task("custom_chain")
        # Default source (3 items), multiplier 3
        # (1*3) + (2*3) + (3*3) = 18
        self.assertEqual(result1, 18)

        reset_pipeline()

        # Then run again with a parameter override for the upstream task
        @Task(name="upstream_override")
        def upstream_override() -> int:
            # This task will pull from data_processor with multiplier=3
            # which in turn will pull from data_source with count=5
            data = uses("data_processor", multiplier=3, count=5)
            return sum(item["value"] for item in data)

        result2 = run_task("upstream_override")
        # 5 items with multiplier 3
        # (1*3) + (2*3) + (3*3) + (4*3) + (5*3) = 45
        self.assertNotEqual(result1, result2)  # Different from previous run

    def test_parameter_caching(self) -> None:
        """Test that tasks with different parameters are cached separately."""
        # Run with multiplier=2
        result1 = run_task("data_processor", multiplier=2)
        # Run with multiplier=3
        result2 = run_task("data_processor", multiplier=3)

        # Verify that results are different because of different parameters
        self.assertNotEqual(
            sum(item["value"] for item in result1),
            sum(item["value"] for item in result2)
        )

        # Verify that running again with the same parameters returns cached results
        result3 = run_task("data_processor", multiplier=2)
        self.assertEqual(result1, result3)


if __name__ == "__main__":
    unittest.main()
