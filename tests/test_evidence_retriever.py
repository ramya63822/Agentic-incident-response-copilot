
from incident_copilot.evidence_retriever import retrieve_evidence


def test_evidence_retrieval():
    results = retrieve_evidence(
        "Payment API database connection failures",
        top_k=3,
    )

    assert results["query"]
    assert "runbooks" in results
    assert "historical_incidents" in results
