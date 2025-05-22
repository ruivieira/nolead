"""Example demonstrating parallel task execution in NoLead."""

import os
import time

from nolead import Task, generate_dependency_graph, parallel, run_task, uses


# Define tasks for our pipeline
@Task()
def load_data():
    """Load raw data for processing."""
    print("Loading data...")
    time.sleep(1)  # Simulate work
    return {"raw_data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}


@Task()
def preprocess_data():
    """Preprocess the data before analysis."""
    data = uses(load_data)
    print("Preprocessing data...")
    time.sleep(1)  # Simulate work
    return {"preprocessed_data": [x * 2 for x in data["raw_data"]]}


@Task()
def calculate_sum():
    """Calculate the sum of preprocessed data."""
    data = uses(preprocess_data)
    print("Calculating sum...")
    time.sleep(2)  # Simulate work
    return {"sum": sum(data["preprocessed_data"])}


@Task()
def calculate_average():
    """Calculate the average of preprocessed data."""
    data = uses(preprocess_data)
    print("Calculating average...")
    time.sleep(2)  # Simulate work
    values = data["preprocessed_data"]
    return {"average": sum(values) / len(values)}


@Task()
def generate_report():
    """Generate a final report by combining the parallel calculation results."""
    # Run the calculations in parallel and get the combined results
    results = parallel([calculate_sum, calculate_average])

    print("Generating report...")
    time.sleep(1)  # Simulate work

    # Create a report from the parallel task results
    report = {
        "sum": results["calculate_sum"]["sum"],
        "average": results["calculate_average"]["average"],
        "timestamp": time.time(),
    }

    print("\nFinal Report:")
    print(f"Sum: {report['sum']}")
    print(f"Average: {report['average']}")

    return report


@Task()
def save_report():
    """Save the report to a file."""
    report = uses(generate_report)
    print("Saving report to file...")
    time.sleep(1)  # Simulate work

    # In a real application, we would save to a file here
    print(f"Report saved with timestamp: {report['timestamp']}")
    return {"status": "success"}


def main():
    """Run the example pipeline and generate a visualization."""
    print("Starting pipeline with parallel tasks...\n")

    # Run the pipeline
    start_time = time.time()
    result = run_task(save_report)
    end_time = time.time()

    print(f"\nPipeline completed in {end_time - start_time:.2f} seconds")
    print(f"Result: {result}")

    # Generate visualizations
    os.makedirs("output", exist_ok=True)
    dot_file = generate_dependency_graph("output/parallel_pipeline.dot")
    text_file = generate_dependency_graph(
        "output/parallel_pipeline.txt", output_format="text"
    )

    print("\nVisualization generated at:")
    print(f"- DOT file: {dot_file}")
    print(f"- Text file: {text_file}")
    print("\nTo convert the DOT file to an image, run:")
    print("  dot -Tpng output/parallel_pipeline.dot -o output/parallel_pipeline.png")


if __name__ == "__main__":
    main()
