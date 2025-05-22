"""Core implementation of the nolead pipeline system."""

import concurrent.futures
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast

from nolead.logging import get_logger

logger = get_logger()

# Registry to store all tasks
_TASKS: Dict[str, "Task"] = {}
# Set to track tasks that have been executed
_EXECUTED_TASKS: Set[str] = set()
# Dictionary to cache task results
_TASK_RESULTS: Dict[str, Any] = {}
# Set to track parallel task groups
_PARALLEL_GROUPS: Dict[str, List[str]] = {}

# Type variables for function return values
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class Task:
    """Decorator that registers a function as a task in the pipeline."""

    def __init__(self, name: Optional[str] = None):
        self.name = name
        self.dependencies: Set[str] = set()
        self.task_func: Optional[Callable[..., Any]] = None
        self.is_parallel_group = False

    def __call__(self, func: F) -> F:
        self.task_func = func
        task_name = self.name or func.__name__
        _TASKS[task_name] = self
        logger.debug("Registered task: %s", task_name)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self.task_func is None:
                raise ValueError(f"Task function is not set for {task_name}")
            return self.task_func(*args, **kwargs)

        wrapper._task = self  # type: ignore
        return cast(F, wrapper)


def uses(task_name_or_func: Any, **kwargs: Any) -> Any:
    """Define a dependency on another task and get its result."""
    if callable(task_name_or_func) and hasattr(task_name_or_func, "_task"):
        task_name = (
            task_name_or_func._task.name or task_name_or_func.__name__
        )  # pylint: disable=protected-access
    else:
        task_name = task_name_or_func

    # Get the calling task
    frame = inspect.currentframe()
    if frame is None:
        logger.warning(
            "Could not get current frame, dependency tracking may not work correctly"
        )
        return run_task(task_name, **kwargs)

    calling_frame = frame.f_back
    if calling_frame is None:
        logger.warning(
            "Could not get caller frame, dependency tracking may not work correctly"
        )
        return run_task(task_name, **kwargs)

    calling_func_name = calling_frame.f_code.co_name

    # Find the task that's calling us
    for task in _TASKS.values():
        if task.task_func and task.task_func.__name__ == calling_func_name:
            task.dependencies.add(task_name)
            logger.debug("Added dependency: %s -> %s", calling_func_name, task_name)
            break

    # Return the result of the dependency
    return run_task(task_name, **kwargs)


def parallel(tasks: List[Union[str, Callable]]) -> Dict[str, Any]:
    """Run multiple tasks in parallel and return their combined results.

    Args:
        tasks: List of task names or task functions to run in parallel

    Returns:
        Dictionary mapping task names to their results
    """
    # Get the calling task to establish dependencies
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        logger.warning("Could not get caller frame, dependency tracking may not work")
    else:
        calling_frame = frame.f_back
        calling_func_name = calling_frame.f_code.co_name

        # Find the task that's calling us
        for task in _TASKS.values():
            if task.task_func and task.task_func.__name__ == calling_func_name:
                # Create dependencies for all parallel tasks
                task_names = []
                for t in tasks:
                    if callable(t) and hasattr(t, "_task"):
                        task_name = t._task.name or t.__name__
                    else:
                        task_name = str(t)
                    task.dependencies.add(task_name)
                    task_names.append(task_name)
                    logger.debug(
                        "Added parallel dependency: %s -> %s",
                        calling_func_name,
                        task_name,
                    )

                # Register this as a parallel group for visualization
                group_name = f"parallel_group_{calling_func_name}"
                _PARALLEL_GROUPS[group_name] = task_names
                break

    # Run the tasks in parallel
    return run_parallel(tasks)


def run_parallel(
    tasks: List[Union[str, Callable]], **shared_params: Any
) -> Dict[str, Any]:
    """Execute multiple tasks in parallel and return their combined results.

    Args:
        tasks: List of task names or task functions to run in parallel
        shared_params: Parameters to pass to all tasks

    Returns:
        Dictionary mapping task names to their results
    """
    task_names: List[str] = []
    task_funcs: List[Tuple[str, Callable[..., Any], Dict[str, Any]]] = []

    # Process task list to get names and functions
    for task in tasks:
        task_name: str
        task_func: Callable[..., Any]

        if callable(task) and hasattr(task, "_task"):
            # Direct callable with task attribute
            task_name = task._task.name or task.__name__
            task_func = task
        else:
            # String task name
            task_name = str(task)
            if task_name not in _TASKS:
                raise ValueError(f"Task '{task_name}' not found")

            # Get task function with explicit None check
            maybe_func = _TASKS[task_name].task_func
            if maybe_func is None:
                raise ValueError(f"Task function is not set for {task_name}")
            task_func = maybe_func

        task_names.append(task_name)
        task_funcs.append((task_name, task_func, shared_params))

    logger.info("Running tasks in parallel: %s", ", ".join(task_names))

    # Execute tasks in parallel using ThreadPoolExecutor
    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_task = {
            executor.submit(run_task, func, **params): name
            for name, func, params in task_funcs
        }

        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future]
            try:
                result = future.result()
                results[task_name] = result
                logger.debug("Parallel task '%s' completed", task_name)
            except Exception as e:
                logger.error("Error in parallel task '%s': %s", task_name, str(e))
                raise

    logger.info("All parallel tasks completed")
    return results


def done(result: Optional[T] = None) -> Optional[T]:
    """Mark a task as done and return its result."""
    return result


def run_task(task_name_or_func: Any, **override_params: Any) -> Any:
    """Run a task and all its dependencies."""
    # Get the task
    if callable(task_name_or_func) and hasattr(task_name_or_func, "_task"):
        task = task_name_or_func._task
        task_name = task.name or task_name_or_func.__name__
    else:
        task_name = task_name_or_func
        if task_name not in _TASKS:
            raise ValueError(f"Task '{task_name}' not found")
        task = _TASKS[task_name]

    # Create a task key that includes parameters
    task_key = task_name
    if override_params:
        param_str = ",".join(f"{k}={v}" for k, v in sorted(override_params.items()))
        task_key = f"{task_name}({param_str})"

    # If already executed with these parameters, return the cached result
    if task_key in _TASK_RESULTS:
        logger.debug(
            "Task '%s' already executed with given parameters, returning cached result",
            task_key,
        )  # noqa: E501
        return _TASK_RESULTS[task_key]

    logger.info("Running task: %s", task_name)

    # Run dependencies first
    for dep in task.dependencies:
        logger.debug("Handling dependency '%s' for task '%s'", dep, task_name)
        run_task(dep)

    # Run the task
    result = None
    if task.task_func is not None:
        try:
            result = task.task_func(**override_params)
            # Cache the result with parameters
            _TASK_RESULTS[task_key] = result
            # Add to executed tasks set
            _EXECUTED_TASKS.add(task_key)
            logger.info("Completed task: %s", task_key)
        except Exception as e:
            logger.error("Error executing task '%s': %s", task_name, str(e))
            raise
    return result


def reset_pipeline() -> None:
    """Reset the executed tasks tracking to allow re-running the pipeline."""
    _EXECUTED_TASKS.clear()
    _TASK_RESULTS.clear()
    _PARALLEL_GROUPS.clear()
    logger.debug("Pipeline execution state reset")
