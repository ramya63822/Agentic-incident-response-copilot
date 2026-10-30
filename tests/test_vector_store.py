
from incident_copilot.vector_store import search_knowledge


def test_semantic_search_returns_results():
    results = search_knowledge(
        "Payment API database connection failures",
        top_k=2,
    )

    assert isinstance(results, list)

    for result in results:
        assert "content" in result
        assert "source" in result
        assert "distance" in result
