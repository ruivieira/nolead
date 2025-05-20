# nolead

A lightweight pipeline orchestration library.

## Features

- Simple task annotation with `@Task()` decorator
- Automatic dependency resolution with `uses()` function
- Clean task completion with `done()` function
- Single entry point to run entire pipelines with `run_task()`

## Installation

```bash
pip install .
```

## Quick Example

```python
from nolead import Task, run_task, uses, done

@Task()
def fetch_data():
    print("Fetching data...")
    return [1, 2, 3, 4, 5]

@Task()
def process_data():
    print("Processing data...")
    # Get result from the dependent task
    data = uses(fetch_data)
    # Process the data
    processed_data = [x * 2 for x in data]
    return done(processed_data)

@Task()
def save_results():
    print("Saving results...")
    # Get result from the dependent task
    processed_data = uses(process_data)
    # Save the results
    print(f"Results saved: {processed_data}")
    return done(True)

if __name__ == "__main__":
    # Execute the pipeline by running the final task
    result = run_task(save_results)
    print(f"Pipeline completed with result: {result}")
```

## Advanced Usage

You can also use named tasks:

```python
@Task(name="fetch_users")
def fetch_users():
    # ... implementation ...
    return users

# Later, refer to the task by name
users = uses("fetch_users")
```

Check out the `examples/` directory for more complex usage scenarios.

## Development

This project uses several development tools to ensure code quality:

- **Ruff**: For linting and code formatting
- **Mypy**: For static type checking
- **Pytest**: For unit testing

### Development Setup

```bash
# Install development dependencies
make deps
```

### Running Tests and Checks

```bash
# Run all checks (lint, type check, tests)
make all

# Run individual checks
make lint    # Run linting
make check   # Run type checking
make test    # Run unit tests

# Clean up project
make clean
```

## License

Apache 2.0 License
