
from incident_copilot.vector_store import search_knowledge


# Manually verified relevant chunk keys.
EVALUATION_DATA = [
    {
        "query": "Database connection timeout",
        "relevant_chunks": [
            "payment_service.md::runbook::0",
            "historical_incidents.json::historical_incident::0",
        ],
    },
    {
        "query": "Payment API HTTP 500 errors",
        "relevant_chunks": [
            "payment_service.md::runbook::0",
            "historical_incidents.json::historical_incident::0",
        ],
    },
    {
        "query": "Safe checks before restarting a service",
        "relevant_chunks": [
            "payment_service.md::runbook::0",
        ],
    },
    {
        "query": "Increasing application latency",
        "relevant_chunks": [
            "payment_service.md::runbook::0",
            "historical_incidents.json::historical_incident::0",
        ],
    },
]


def get_chunk_key(result):
    metadata = result["metadata"]

    return (
        f'{metadata["source"]}::'
        f'{metadata["type"]}::'
        f'{metadata["chunk_index"]}'
    )


def evaluate_retrieval(k=2):
    precision_scores = []
    recall_scores = []
    reciprocal_ranks = []

    for item in EVALUATION_DATA:

        results = search_knowledge(
            item["query"],
            top_k=k,
            max_per_source=3,
            max_distance=2.0,
        )

        relevant = set(item["relevant_chunks"])

        retrieved = [
            get_chunk_key(result)
            for result in results
        ]

        relevant_retrieved = len(
            set(retrieved) & relevant
        )

        precision = relevant_retrieved / k
        recall = relevant_retrieved / len(relevant)

        reciprocal_rank = 0

        for rank, chunk in enumerate(retrieved, start=1):
            if chunk in relevant:
                reciprocal_rank = 1 / rank
                break

        precision_scores.append(precision)
        recall_scores.append(recall)
        reciprocal_ranks.append(reciprocal_rank)

        print("\n" + "=" * 60)
        print("QUERY:", item["query"])

        for rank, result in enumerate(results, start=1):
            print(f"\nRank: {rank}")
            print("Chunk:", get_chunk_key(result))
            print("Distance:", round(result["distance"], 4))
            print("Relevant:", get_chunk_key(result) in relevant)

        print("\nPrecision@K:", round(precision, 3))
        print("Recall@K:", round(recall, 3))
        print("Reciprocal Rank:", round(reciprocal_rank, 3))

    count = len(EVALUATION_DATA)

    print("\n" + "=" * 60)
    print("FINAL RAG EVALUATION")

    print(
        "Mean Precision@K:",
        round(sum(precision_scores) / count, 3),
    )

    print(
        "Mean Recall@K:",
        round(sum(recall_scores) / count, 3),
    )

    print(
        "MRR:",
        round(sum(reciprocal_ranks) / count, 3),
    )


if __name__ == "__main__":
    evaluate_retrieval()
