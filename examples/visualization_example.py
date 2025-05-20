"""Example demonstrating visualization capabilities of the nolead pipeline system."""

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


# Define some tasks for our pipeline
@Task(name="task_a")
def task_a():
    """Execute task A and return its result."""
    print("Executing task A")
    return "result_a"


@Task(name="task_b")
def task_b():
    """Execute task B and return its result."""
    print("Executing task B")
    return "result_b"


@Task(name="task_c")
def task_c():
    """Execute task C, which depends on task A."""
    print("Executing task C")
    a_result = uses("task_a")
    return done(f"C processed {a_result}")


@Task(name="task_d")
def task_d():
    """Execute task D, which depends on tasks B and C."""
    print("Executing task D")
    b_result = uses("task_b")
    c_result = uses("task_c")
    return done(f"D combined {b_result} and {c_result}")


@Task(name="task_e")
def task_e():
    """Execute task E, which depends on task D."""
    print("Executing task E")
    d_result = uses("task_d")
    return done(f"E finalized {d_result}")


if __name__ == "__main__":
    print("\n=== Pipeline Visualization Example ===\n")

    # Execute the pipeline first to register dependencies
    print("=== Executing Pipeline to Register Dependencies ===")
    result = run_task("task_e")
    print(f"Pipeline result: {result}\n")

    # Reset pipeline for a clean state
    reset_pipeline()

    # Generate a DOT file for the entire pipeline
    dot_file = generate_dependency_graph("pipeline.dot", output_format="dot")
    print(f"Generated DOT file: {dot_file}")
    print(
        "You can visualize this with Graphviz: dot -Tpng pipeline.dot -o pipeline.png\n"
    )

    # Generate a text representation of the dependencies
    text_file = generate_dependency_graph("pipeline.txt", output_format="text")
    print(f"Generated text file: {text_file}")

    # Print detailed information about a specific task
    print("\n=== Task Information ===")
    print_task_info("task_d")

    # Execute the pipeline again to show it working
    print("\n=== Executing Pipeline Again ===")
    result = run_task("task_e")
    print(f"\nFinal result: {result}")

    # Reset and run again
    print("\n=== Resetting and Running Again ===")
    reset_pipeline()
    result = run_task("task_e")
    print(f"\nFinal result (after reset): {result}")
