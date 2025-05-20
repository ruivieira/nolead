.PHONY: lint check test clean all

# Default target
all: lint check test

# Install development dependencies
deps:
	pip install -e .
	pip install ruff mypy pytest

# Run linting with ruff
lint:
	ruff check .

# Run type checking with mypy
check:
	mypy nolead tests

# Run unit tests with pytest
test:
	pytest

# Run all checks and tests
check-all: lint check test

# Clean up Python artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyi" -delete

# Help target
help:
	@echo "Available targets:"
	@echo "  all        Run lint, check, and test"
	@echo "  deps       Install development dependencies"
	@echo "  lint       Run linting with ruff"
	@echo "  check      Run type checking with mypy"
	@echo "  test       Run unit tests with pytest"
	@echo "  check-all  Run lint, check, and test (same as all)"
	@echo "  clean      Remove build artifacts and cache files"
	@echo "  help       Show this help message"
