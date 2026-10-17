
from incident_copilot.evidence_retriever import retrieve_evidence


def main():
    query = (
        "payment API HTTP 500 errors and database "
        "connection timeout"
    )

    results = retrieve_evidence(query, top_k=3)

    print("\n=== EVIDENCE RETRIEVAL TEST ===")
    print(f"Query: {results['query']}")

    print("\n--- Relevant Runbooks ---")

    if results["runbooks"]:
        for item in results["runbooks"]:
            print(f"\nSource: {item['source']}")
            print(f"Relevance score: {item['relevance_score']}")
            print(item["content"][:1000])
    else:
        print("No matching runbooks found.")

    print("\n--- Relevant Historical Incidents ---")

    if results["historical_incidents"]:
        for item in results["historical_incidents"]:
            print(f"\nSource: {item['source']}")
            print(f"Relevance score: {item['relevance_score']}")
            print(item["content"])
    else:
        print("No matching historical incidents found.")


if __name__ == "__main__":
    main()
