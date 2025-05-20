"""Simple example demonstrating a basic pipeline with nolead."""

from nolead import Task, done, run_task, uses


@Task()
def fetch_data():
    """Fetch raw data from source."""
    print("Fetching data...")
    # In a real scenario, we would fetch data from some source
    return [1, 2, 3, 4, 5]


@Task()
def process_data():
    """Process the data from fetch_data task."""
    print("Processing data...")
    # Get result from the dependent task
    data = uses(fetch_data)
    # Process the data
    processed_data = [x * 2 for x in data]
    return done(processed_data)


@Task()
def save_results():
    """Save processed data to destination."""
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
