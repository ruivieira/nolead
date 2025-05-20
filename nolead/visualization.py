"""Visualization utilities for task dependency graphs and pipeline information."""

import datetime
from typing import Dict, List, Optional, Set

from nolead.core import _TASKS
from nolead.logging import get_logger

logger = get_logger()


def generate_dependency_graph(
    output_file: str = "pipeline_graph.dot",
    include_tasks: Optional[List[str]] = None,
    output_format: str = "dot",
) -> str:
    """Generate a dependency graph for the pipeline tasks.

    Args:
        output_file: Path to save the output file
        include_tasks: List of task names to include (None for all)
        output_format: Output format ('dot' for Graphviz DOT, 'text' for text representation)

    Returns:
        Path to the generated file
    """  # noqa: E501
    logger.info("Generating dependency graph in %s format", output_format)

    if output_format == "dot":
        return _generate_dot_graph(output_file, include_tasks)
    elif output_format == "text":
        return _generate_text_graph(output_file, include_tasks)
    else:
        raise ValueError(f"Unsupported format: {output_format}")


def _generate_dot_graph(output_file: str, include_tasks: Optional[List[str]]) -> str:
    """Generate a Graphviz DOT file for the pipeline."""
    tasks_to_include = set(include_tasks) if include_tasks else set(_TASKS.keys())

    # Get current timestamp for the header
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Analyze task dependencies to identify source, intermediate, and sink nodes
    dependencies_map: Dict[str, Set[str]] = {}
    dependents_map: Dict[str, Set[str]] = {}

    # Initialize maps
    for task_name in tasks_to_include:
        if task_name in _TASKS:
            dependencies_map[task_name] = set()
            dependents_map[task_name] = set()

    # Fill dependency and dependent maps
    for task_name, task in _TASKS.items():
        if task_name in tasks_to_include:
            # Get dependencies
            dependencies = set()
            for dep in task.dependencies:
                if dep in tasks_to_include:
                    dependencies.add(dep)
            dependencies_map[task_name] = dependencies

            # Update dependents
            for dep in dependencies:
                if dep in dependents_map:
                    dependents_map[dep].add(task_name)

    # Identify sources, intermediates, and sinks
    sources = []
    intermediates = []
    sinks = []

    for task_name in tasks_to_include:
        if task_name in dependencies_map and task_name in dependents_map:
            if not dependencies_map[task_name]:  # No dependencies
                sources.append(task_name)
            elif not dependents_map[task_name]:  # No dependents
                sinks.append(task_name)
            else:
                intermediates.append(task_name)

    # Create DOT file content
    dot_content = ["digraph G {"]
    dot_content.append("  // Graph settings")
    dot_content.append("  rankdir=LR;")
    dot_content.append('  bgcolor="#FFFDF5";')
    dot_content.append('  fontname="Arial";')
    dot_content.append("  concentrate=true;")  # Merge edges
    dot_content.append("  nodesep=0.5;")
    dot_content.append("  ranksep=0.8;")
    dot_content.append("  splines=curved;")  # Curved edges

    # Add header as a special node
    dot_content.append("  // Header")
    dot_content.append('  labelloc="t";')
    dot_content.append('  label="NoLead Pipeline\\nGenerated: ' + timestamp + '";')
    dot_content.append("  fontsize=16;")

    # Define common node styling
    dot_content.append("  // Common node styling")
    dot_content.append("  node [")
    dot_content.append("    shape=box,")
    dot_content.append('    style="filled,rounded",')  # Rounded rectangles
    dot_content.append('    fontname="Arial",')
    dot_content.append("    fontsize=12,")
    dot_content.append("    height=0.4,")
    dot_content.append('    margin="0.3,0.2",')
    dot_content.append('    color="#999999"')  # Border color
    dot_content.append("  ];")

    # Define edge styling
    dot_content.append("  // Edge styling")
    dot_content.append("  edge [")
    dot_content.append('    color="#666666",')
    dot_content.append("    arrowsize=0.8,")
    dot_content.append("    penwidth=1.2")
    dot_content.append("  ];")

    # Add source nodes (green)
    dot_content.append("  // Source nodes")
    dot_content.append("  { rank=same; ")
    for task_name in sources:
        dot_content.append(f'    "{task_name}" [fillcolor="#CCFFCC"];')  # Light green
    dot_content.append("  }")

    # Add intermediate nodes (yellow)
    dot_content.append("  // Intermediate nodes")
    for task_name in intermediates:
        dot_content.append(f'  "{task_name}" [fillcolor="#FFFFAA"];')  # Light yellow

    # Add sink nodes (light blue)
    dot_content.append("  // Sink nodes")
    dot_content.append("  { rank=same; ")
    for task_name in sinks:
        dot_content.append(f'    "{task_name}" [fillcolor="#CCECFF"];')  # Light blue
    dot_content.append("  }")

    # Add edges
    dot_content.append("  // Edges")
    for task_name, task in _TASKS.items():
        if task_name in tasks_to_include:
            for dep in task.dependencies:
                if dep in tasks_to_include:
                    dot_content.append(f'  "{dep}" -> "{task_name}";')

    dot_content.append("}")

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(dot_content))

    logger.info("Dependency graph generated at %s", output_file)
    return output_file


def _generate_text_graph(output_file: str, include_tasks: Optional[List[str]]) -> str:
    """Generate a text representation of the dependency graph."""
    tasks_to_include = set(include_tasks) if include_tasks else set(_TASKS.keys())

    # Create the graph content
    text_content = ["Pipeline Dependency Graph", "========================", ""]

    # Build a dependency tree
    for task_name in sorted(tasks_to_include):
        if task_name in _TASKS:
            text_content.append(f"Task: {task_name}")

            # List dependencies
            deps = [
                dep for dep in _TASKS[task_name].dependencies if dep in tasks_to_include
            ]
            if deps:
                text_content.append("  Dependencies:")
                for dep in sorted(deps):
                    text_content.append(f"    - {dep}")
            else:
                text_content.append("  Dependencies: None")

            text_content.append("")  # Empty line between tasks

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(text_content))

    logger.info("Text dependency graph generated at %s", output_file)
    return output_file


def print_task_info(task_name: str) -> None:
    """Print detailed information about a specific task."""
    if task_name not in _TASKS:
        logger.error("Task '%s' not found", task_name)
        return

    task = _TASKS[task_name]
    print(f"Task: {task_name}")
    print(f"Function: {task.task_func.__name__ if task.task_func else 'None'}")
    print(f"Dependencies ({len(task.dependencies)}):")

    for dep in sorted(task.dependencies):
        print(f"  - {dep}")

    # Find tasks that depend on this task
    dependents = []
    for name, t in _TASKS.items():
        if task_name in t.dependencies:
            dependents.append(name)

    print(f"Dependents ({len(dependents)}):")
    for dep in sorted(dependents):
        print(f"  - {dep}")
