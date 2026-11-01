
from incident_copilot.vector_store import search_knowledge


EVALUATION_QUERIES = [
    "Database connection pool exhaustion",
    "Payment API HTTP 500 errors",
    "Increasing application latency",
    "Safe checks before restarting a service",
    "Database connection timeout",
]


def evaluate_retrieval():
    for query in EVALUATION_QUERIES:
        print("\n" + "=" * 70)
        print("QUERY:", query)

        results = search_knowledge(query, top_k=3)

        if not results:
            print("No results retrieved.")
            continue

        for rank, result in enumerate(results, start=1):
            print(f"\nRank: {rank}")
            print("Source:", result["source"])
            print("Type:", result["type"])
            print("Distance:", round(result["distance"], 4))
            print("Content:", result["content"][:300])


if __name__ == "__main__":
    evaluate_retrieval()
