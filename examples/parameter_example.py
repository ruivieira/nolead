"""Example demonstrating task parameter passing in nolead."""

from typing import Any, Dict, List, Union, cast

from nolead import Task, reset_pipeline, run_task, uses


@Task(name="fetch_data")
def fetch_data(source: str = "database", limit: int = 10, format: str = "json") -> Union[List[Dict[str, Any]], List[int]]:  # noqa: E501, FA100
    """Fetch data from a source with configurable parameters."""
    print(f"Fetching data from {source} (limit: {limit}, format: {format})...")

    # Simulate different data based on source
    if source == "database":
        data: Union[List[Dict[str, Any]], List[int]] = [
            {"id": i, "value": i * 10} for i in range(1, limit + 1)
        ]
    elif source == "api":
        data = [{"id": i, "name": f"Item {i}"} for i in range(1, limit + 1)]
    elif source == "file":
        data = list(range(1, limit + 1))
    else:
        data = []

    print(f"Fetched {len(data)} records")
    return data


@Task(name="transform_data")
def transform_data(transformation: str = "double") -> List[Dict[str, Any]]:
    """Transform data with configurable transformation strategy."""
    print(f"Transforming data using '{transformation}' strategy...")

    # Get data from the upstream task with specific parameters
    data = cast(List[Dict[str, Any]], uses("fetch_data", source="api", limit=5))

    # Apply transformation based on parameter
    if transformation == "double":
        result = [{"id": item["id"], "name": item["name"], "value": item["id"] * 2}
                 for item in data]
    elif transformation == "square":
        result = [{"id": item["id"], "name": item["name"], "value": item["id"] ** 2}
                 for item in data]
    else:
        result = data

    print(f"Transformed {len(result)} records")
    return result


@Task(name="aggregate_data")
def aggregate_data(method: str = "sum") -> Union[int, float]:
    """Aggregate the transformed data using a specified method."""
    print(f"Aggregating data using '{method}' method...")

    # Get data from upstream task with specific parameters
    data = uses("transform_data", transformation="square")

    # Aggregate based on method parameter
    if method == "sum":
        result: Union[int, float] = sum(item["value"] for item in data)
    elif method == "avg":
        result = sum(item["value"] for item in data) / len(data)
    elif method == "max":
        result = max(item["value"] for item in data)
    else:
        result = 0

    print(f"Aggregation result: {result}")
    return result


def main() -> None:
    """Run the pipeline with different parameter combinations."""
    print("\n=== Pipeline Run 1: Default Parameters ===")
    result1 = run_task("aggregate_data")
    print(f"Final result: {result1}")

    reset_pipeline()

    print("\n=== Pipeline Run 2: Custom Parameters ===")
    result2 = run_task("aggregate_data", method="avg")
    print(f"Final result: {result2}")

    reset_pipeline()

    print("\n=== Pipeline Run 3: Direct Parameter Passing ===")
    # Running task with direct parameter specification
    result3 = run_task("fetch_data", source="file", limit=3, format="csv")
    print(f"Direct fetch result: {result3}")


if __name__ == "__main__":
    main()
