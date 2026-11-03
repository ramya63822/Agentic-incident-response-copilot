
import json
from types import SimpleNamespace

from incident_copilot import investigation_graph as graph_module


def test_complete_investigation_graph(monkeypatch):
    """Test all LangGraph nodes using mocked RAG and Groq."""

    # Mock RAG retrieval.
    def mock_retrieve_evidence(query, top_k=3):
        return {
            "query": query,
            "runbooks": [
                {
                    "source": "payment_service.md",
                    "content": "Check database health.",
                    "distance": 0.2,
                    "type": "runbook",
                    "metadata": {"source": "payment_service.md"},
                    "relevance_score": 0.8,
                }
            ],
            "historical_incidents": [],
        }

    monkeypatch.setattr(
        graph_module,
        "retrieve_evidence",
        mock_retrieve_evidence,
    )

    # Mock Groq response.
    mock_report = {
        "incident_summary": "Simulated payment failure.",
        "observed_facts": ["HTTP 500 failure detected."],
        "possible_causes": ["Intentional failure injection."],
        "recommended_checks": ["Verify the test scenario."],
        "root_cause_confirmed": False,
        "limitations": ["Only simulated logs were supplied."],
    }

    mock_usage = SimpleNamespace(
        prompt_tokens=100,
        completion_tokens=150,
        total_tokens=250,
    )

    mock_message = SimpleNamespace(
        content=json.dumps(mock_report)
    )

    mock_choice = SimpleNamespace(
        message=mock_message
    )

    mock_response = SimpleNamespace(
        choices=[mock_choice],
        usage=mock_usage,
    )

    class MockCompletions:
        def create(self, **kwargs):
            return mock_response

    class MockChat:
        completions = MockCompletions()

    class MockGroq:
        def __init__(self, api_key):
            self.chat = MockChat()

    monkeypatch.setattr(
        graph_module,
        "Groq",
        MockGroq,
    )

    monkeypatch.setattr(
        graph_module,
        "os",
        SimpleNamespace(
            getenv=lambda key, default=None: (
                "fake-test-key"
                if key == "GROQ_API_KEY"
                else default
            )
        ),
    )

    # Execute the complete graph.
    graph = graph_module.build_investigation_graph()

    result = graph.invoke({
        "incident": {
            "title": "Payment API failures",
            "service": "payment-api",
            "description": "Repeated HTTP 500 errors.",
            "severity": "High",
        },
        "current_logs": [
            "ERROR status=500 reason=simulated_failure"
        ],
    })

    # Verify the complete workflow output.
    report = result["report"]

    assert report["incident_summary"] == (
        "Simulated payment failure."
    )

    assert report["incident_classification"]["classification"] == (
        "simulated"
    )

    assert report["failure_injection_detected"] is True

    assert report["root_cause_confirmed"] is False

    assert report["model"] == "openai/gpt-oss-20b"

    assert report["usage"]["total_tokens"] == 250

    assert len(report["evidence_sources"]["runbooks"]) == 1
