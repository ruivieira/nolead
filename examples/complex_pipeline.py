import time

from nolead import Task, done, run_task, uses


@Task(name="fetch_users")
def fetch_users():
    print("Fetching users data...")
    time.sleep(0.5)  # Simulate network delay
    return ["user1", "user2", "user3"]


@Task(name="fetch_products")
def fetch_products():
    print("Fetching products data...")
    time.sleep(0.5)  # Simulate network delay
    return ["product1", "product2", "product3"]


@Task(name="process_users")
def process_users():
    print("Processing users...")
    users = uses("fetch_users")
    processed_users = [f"processed_{user}" for user in users]
    return done(processed_users)


@Task(name="process_products")
def process_products():
    print("Processing products...")
    products = uses("fetch_products")
    processed_products = [f"processed_{product}" for product in products]
    return done(processed_products)


@Task(name="merge_data")
def merge_data():
    print("Merging data...")
    users = uses("process_users")
    products = uses("process_products")

    # Create a simple mapping between users and products
    result = {}
    for i, user in enumerate(users):
        if i < len(products):
            result[user] = products[i]
        else:
            result[user] = None

    return done(result)


@Task(name="generate_report")
def generate_report():
    print("Generating final report...")
    merged_data = uses("merge_data")

    # Generate a report from the merged data
    report = ["=== FINAL REPORT ==="]
    for user, product in merged_data.items():
        report.append(f"{user} assigned to {product}")
    report.append("===================")

    return done("\n".join(report))


if __name__ == "__main__":
    print("Starting pipeline execution...")
    start_time = time.time()

    # Execute the pipeline
    report = run_task("generate_report")

    end_time = time.time()
    print(f"\nExecution time: {end_time - start_time:.2f} seconds")
    print("\nFinal Report:")
    print(report)
