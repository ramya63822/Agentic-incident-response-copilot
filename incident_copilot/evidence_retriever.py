
"""Retrieve operational knowledge using ChromaDB semantic search."""

from incident_copilot.vector_store import search_knowledge


def retrieve_evidence(
    query: str,
    top_k: int = 3,
) -> dict:
    """Retrieve relevant runbooks and historical incidents."""

    if not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    results = search_knowledge(query, top_k=top_k)

    runbooks = []
    historical_incidents = []

    for result in results:
        evidence = {
            "source": result["source"],
            "content": result["content"],
            "relevance_score": round(
                1 - result["distance"], 4
            ),
            "distance": result["distance"],
            "type": result["type"],
            "metadata": result["metadata"],
        }

        if result["type"] == "runbook":
            runbooks.append(evidence)

        elif result["type"] == "historical_incident":
            historical_incidents.append(evidence)

    return {
        "query": query,
        "runbooks": runbooks,
        "historical_incidents": historical_incidents,
    }
