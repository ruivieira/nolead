"""Example demonstrating visualization of task parameters in the nolead pipeline system."""

import os
import subprocess
from nolead import (
    LogLevel,
    Task,
    configure_logging,
    done,
    generate_dependency_graph,
    print_task_info,
    reset_pipeline,
    run_task,
    uses,
)

# Configure logging to see what's happening
configure_logging(LogLevel.INFO)


# Define tasks with parameters
@Task(name="fetch_data")
def fetch_data(source: str = "database", limit: int = 10):
    """Fetch data from a source with configurable parameters."""
    print(f"Fetching data from {source} (limit: {limit})...")
    data = [{"id": i, "value": i * 10} for i in range(1, limit + 1)]
    print(f"Fetched {len(data)} records")
    return data


@Task(name="process_data")
def process_data(transformation: str = "double"):
    """Process data with a transformation parameter."""
    print(f"Processing data with transformation: {transformation}")
    # Use specific parameters when fetching upstream task result
    data = uses("fetch_data", source="api", limit=5)
    
    # Apply transformation
    if transformation == "double":
        result = [{"id": item["id"], "value": item["value"] * 2} for item in data]
    elif transformation == "square":
        result = [{"id": item["id"], "value": item["value"] ** 2} for item in data]
    else:
        result = data
        
    return done(result)


@Task(name="analyze_data")
def analyze_data(method: str = "sum"):
    """Analyze data with a specific method parameter."""
    print(f"Analyzing data with method: {method}")
    # Use specific parameters for upstream task
    data = uses("process_data", transformation="square")
    
    if method == "sum":
        result = sum(item["value"] for item in data)
    elif method == "avg":
        result = sum(item["value"] for item in data) / len(data)
    elif method == "max":
        result = max(item["value"] for item in data)
    else:
        result = 0
        
    return done(result)


@Task(name="format_results")
def format_results(format_type: str = "text"):
    """Format results in a specific format."""
    print(f"Formatting results as {format_type}")
    # Use specific parameters for upstream task
    value = uses("analyze_data", method="avg")
    
    if format_type == "text":
        return done(f"The result is {value}")
    elif format_type == "json":
        return done({"result": value})
    else:
        return done(str(value))


if __name__ == "__main__":
    print("\n=== Parameter Visualization Example ===\n")

    # Execute the pipeline to register dependencies with parameters
    print("=== Executing Pipeline to Register Dependencies ===")
    result = run_task("format_results", format_type="json")
    print(f"Pipeline result: {result}\n")

    # Generate DOT file showing the parameter connections
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    dot_file = os.path.join(docs_dir, "parameter_graph.dot")
    generate_dependency_graph(dot_file, output_format="dot")
    print(f"Generated DOT file: {dot_file}")
    
    # Try to generate PNG if graphviz is installed
    try:
        png_file = os.path.join(docs_dir, "parameter_graph.png")
        subprocess.run(["dot", "-Tpng", dot_file, "-o", png_file], check=True)
        print(f"Generated PNG file: {png_file}")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Could not generate PNG. Make sure Graphviz is installed.")
    
    # Print detailed information about a specific task
    print("\n=== Task Information with Parameters ===")
    print_task_info("analyze_data") 