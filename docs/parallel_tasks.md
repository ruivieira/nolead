# Parallel Task Execution

NoLead now supports running multiple tasks in parallel, which can significantly improve performance for tasks that can be executed independently.

## Overview

The parallel task execution feature allows you to:

1. Run multiple independent tasks concurrently
2. Automatically track dependencies between parallel tasks and the rest of the pipeline
3. Visualize parallel task groups in the pipeline graph
4. Merge results from parallel tasks into a single dictionary

## Basic Usage

To execute tasks in parallel, use the `parallel()` function:

```python
from nolead import Task, uses, parallel

@Task()
def task1():
    return {"result": "data from task1"}

@Task()
def task2():
    return {"result": "data from task2"}

@Task()
def combined_task():
    # Run task1 and task2 in parallel
    results = parallel([task1, task2])

    # Access results from each task
    task1_result = results["task1"]["result"]
    task2_result = results["task2"]["result"]

    return {"combined": f"{task1_result} + {task2_result}"}
```

## Result Format

When using `parallel()`, the results are returned as a dictionary where:
- Keys are the task names
- Values are the return values from each task

For example:

```python
results = parallel([task1, task2, task3])
# Results will be:
# {
#   "task1": {"result": "data from task1"},
#   "task2": {"result": "data from task2"},
#   "task3": {"result": "data from task3"}
# }
```

## Dependencies

The `parallel()` function automatically handles dependencies:

1. Tasks specified in the parallel list are executed concurrently
2. Any dependencies of those tasks are executed first (serially or in parallel as appropriate)
3. The calling task will be set as dependent on all parallel tasks

For example:

```python
@Task()
def load_data():
    return {"data": [1, 2, 3, 4, 5]}

@Task()
def process1():
    data = uses(load_data)  # Dependency on load_data
    return {"sum": sum(data["data"])}

@Task()
def process2():
    data = uses(load_data)  # Dependency on load_data
    return {"product": 1}

@Task()
def final_task():
    # process1 and process2 will run in parallel
    # load_data will run first as it's a dependency of both
    results = parallel([process1, process2])
    return {
        "sum": results["process1"]["sum"],
        "product": results["process2"]["product"]
    }
```

## Visualization

Parallel tasks are visualized with special styling in the dependency graph:

1. DOT format:
   - Parallel tasks are grouped in a subgraph with a dashed border
   - Edges connecting to parallel task groups have a dashed, bold style

2. Text format:
   - Parallel tasks are listed as a separate section
   - Tasks that are part of parallel groups are marked with `[parallel]`

### Example Visualization

To generate a visualization with parallel tasks:

```python
from nolead import generate_dependency_graph

# Generate DOT file for visualization with Graphviz
generate_dependency_graph("pipeline_with_parallel.dot")

# Generate text representation
generate_dependency_graph("pipeline_with_parallel.txt", output_format="text")
```

You can convert the DOT file to an image using Graphviz:

```bash
dot -Tpng pipeline_with_parallel.dot -o pipeline_with_parallel.png
```

## Advanced Usage: Shared Parameters

You can also use the lower-level `run_parallel()` function to pass shared parameters to all parallel tasks:

```python
from nolead import run_parallel

results = run_parallel([task1, task2, task3], param1="value", param2=42)
```

This will pass `param1="value"` and `param2=42` to all three tasks.

## Performance Considerations

Parallel execution is most beneficial when:

1. Tasks involve I/O operations (network requests, file operations)
2. Tasks are computationally intensive
3. Tasks are independent of each other or share only common dependencies

Note that parallel execution uses Python's `ThreadPoolExecutor`, which is subject to the Global Interpreter Lock (GIL). For CPU-bound tasks, you might not see a significant performance improvement unless the tasks are releasing the GIL (e.g., by using NumPy, which uses C extensions that release the GIL).

## Example Pipeline

Here's a complete example of a pipeline using parallel tasks:

```python
from nolead import Task, uses, parallel, run_task

@Task()
def load_data():
    return {"raw_data": [1, 2, 3, 4, 5]}

@Task()
def preprocess():
    data = uses(load_data)
    return {"processed": [x * 2 for x in data["raw_data"]]}

@Task()
def calculate_sum():
    data = uses(preprocess)
    return {"sum": sum(data["processed"])}

@Task()
def calculate_average():
    data = uses(preprocess)
    values = data["processed"]
    return {"average": sum(values) / len(values)}

@Task()
def generate_report():
    # Run calculations in parallel
    results = parallel([calculate_sum, calculate_average])

    return {
        "sum": results["calculate_sum"]["sum"],
        "average": results["calculate_average"]["average"]
    }

# Run the pipeline
result = run_task(generate_report)
print(result)  # {"sum": 30, "average": 6.0}
```

In this example, `calculate_sum` and `calculate_average` will run in parallel, both using the output from `preprocess`.
