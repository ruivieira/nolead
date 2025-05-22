"""Visualization utilities for task dependency graphs and pipeline information."""

import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from nolead.core import _PARALLEL_GROUPS, _TASK_RESULTS, _TASKS
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


def _extract_task_parameters() -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Extract parameters passed between tasks from the task results cache.

    Returns:
        A dictionary with (source_task, target_task) tuples as keys and parameter
        dictionaries as values
    """
    parameters = {}

    # Process task keys that include parameters
    for task_key in _TASK_RESULTS:
        if "(" in task_key:
            task_name = task_key.split("(")[0]
            param_str = task_key.split("(")[1].rstrip(")")

            # Parse parameters
            params = {}
            if param_str:
                param_pairs = param_str.split(",")
                for pair in param_pairs:
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        params[k] = v

            # Find task dependencies that use this task
            for other_task_name, task in _TASKS.items():
                if task_name in task.dependencies:
                    parameters[(task_name, other_task_name)] = params

    return parameters


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

    # Extract parameters passed between tasks
    task_parameters = _extract_task_parameters()

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
    dot_content.append("  concentrate=false;")  # Don't merge edges to show parameters
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
    dot_content.append("    penwidth=1.2,")
    dot_content.append('    fontname="Arial",')
    dot_content.append("    fontsize=10")
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

    # Create subgraphs for parallel task groups
    if _PARALLEL_GROUPS:
        dot_content.append("  // Parallel task groups")
        for group_idx, (_, group_tasks) in enumerate(_PARALLEL_GROUPS.items()):
            # Filter to only include tasks that are in our visualization
            included_tasks = [t for t in group_tasks if t in tasks_to_include]
            if included_tasks:
                subgraph_name = f"cluster_parallel_{group_idx}"
                dot_content.append(f"  subgraph {subgraph_name} {{")
                dot_content.append('    label="Parallel Tasks";')
                dot_content.append('    style="rounded,dashed";')
                dot_content.append('    color="#5555AA";')
                dot_content.append('    fontcolor="#5555AA";')
                dot_content.append('    bgcolor="#F0F0FF";')  # Light blue background
                # Make sure the parallel tasks are at the same rank
                dot_content.append("    { rank=same; ")
                for task_name in included_tasks:
                    dot_content.append(f'      "{task_name}";')
                dot_content.append("    }")
                dot_content.append("  }")

    # Add edges with parameters
    dot_content.append("  // Edges")
    for task_name, task in _TASKS.items():
        if task_name in tasks_to_include:
            for dep in task.dependencies:
                if dep in tasks_to_include:
                    # Check if we have parameters for this connection
                    edge_params = task_parameters.get((dep, task_name), {})

                    # Check if this is part of a parallel group
                    is_parallel_edge = False
                    for group_tasks in _PARALLEL_GROUPS.values():
                        if dep in group_tasks and task_name not in group_tasks:
                            is_parallel_edge = True
                            break

                    # Set edge style based on whether it's part of a parallel group
                    edge_style = ""
                    if is_parallel_edge:
                        edge_style = ' style="bold,dashed" color="#5555AA" penwidth=1.5'

                    if edge_params:
                        # Format parameters as a label
                        param_label = ", ".join(
                            [f"{k}={v}" for k, v in edge_params.items()]
                        )
                        dot_content.append(
                            f'  "{dep}" -> "{task_name}" [label="{param_label}"{edge_style}];'  # noqa: E501
                        )
                    else:
                        dot_content.append(f'  "{dep}" -> "{task_name}"{edge_style};')

    dot_content.append("}")

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(dot_content))

    logger.info("Dependency graph generated at %s", output_file)
    return output_file


def _generate_text_graph(output_file: str, include_tasks: Optional[List[str]]) -> str:
    """Generate a text representation of the dependency graph."""
    tasks_to_include = set(include_tasks) if include_tasks else set(_TASKS.keys())

    # Extract parameters passed between tasks
    task_parameters = _extract_task_parameters()

    # Create the graph content
    text_content = ["Pipeline Dependency Graph", "========================", ""]

    # Add information about parallel task groups
    if _PARALLEL_GROUPS:
        text_content.append("Parallel Task Groups:")
        for group_idx, (_, group_tasks) in enumerate(_PARALLEL_GROUPS.items()):
            # Filter to only include tasks that are in our visualization
            included_tasks = [t for t in group_tasks if t in tasks_to_include]
            if included_tasks:
                text_content.append(
                    f"  Group {group_idx + 1}: {', '.join(included_tasks)}"
                )
        text_content.append("")  # Empty line

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
                    # Check if we have parameters for this connection
                    edge_params = task_parameters.get((dep, task_name), {})

                    # Check if this is part of a parallel group
                    is_parallel = False
                    for group_tasks in _PARALLEL_GROUPS.values():
                        if dep in group_tasks and task_name not in group_tasks:
                            is_parallel = True
                            break

                    # Add a marker for parallel tasks
                    parallel_marker = " [parallel]" if is_parallel else ""

                    if edge_params:
                        param_str = ", ".join(
                            [f"{k}={v}" for k, v in edge_params.items()]
                        )
                        text_content.append(
                            f"    - {dep}{parallel_marker} (params: {param_str})"
                        )
                    else:
                        text_content.append(f"    - {dep}{parallel_marker}")
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

    # Extract parameters for this task's dependencies
    task_parameters = _extract_task_parameters()

    # Check if this task is part of any parallel groups
    in_parallel_groups = []
    for group_name, group_tasks in _PARALLEL_GROUPS.items():
        if task_name in group_tasks:
            in_parallel_groups.append((group_name, group_tasks))

    if in_parallel_groups:
        print("Parallel Groups:")
        for group_name, group_tasks in in_parallel_groups:
            print(f"  - {group_name}: {', '.join(sorted(group_tasks))}")

    for dep in sorted(task.dependencies):
        # Check if we have parameters for this dependency
        edge_params = task_parameters.get((dep, task_name), {})

        # Check if this is a parallel dependency
        is_parallel = False
        for _, group_tasks in in_parallel_groups:
            if dep in group_tasks:
                is_parallel = True
                break

        parallel_marker = " [parallel]" if is_parallel else ""

        if edge_params:
            param_str = ", ".join([f"{k}={v}" for k, v in edge_params.items()])
            print(f"  - {dep}{parallel_marker} (params: {param_str})")
        else:
            print(f"  - {dep}{parallel_marker}")

    # Find tasks that depend on this task
    dependents = []
    for name, t in _TASKS.items():
        if task_name in t.dependencies:
            dependents.append(name)

    print(f"Dependents ({len(dependents)}):")
    for dep in sorted(dependents):
        # Check if we have parameters for this dependent
        edge_params = task_parameters.get((task_name, dep), {})
        if edge_params:
            param_str = ", ".join([f"{k}={v}" for k, v in edge_params.items()])
            print(f"  - {dep} (params: {param_str})")
        else:
            print(f"  - {dep}")
