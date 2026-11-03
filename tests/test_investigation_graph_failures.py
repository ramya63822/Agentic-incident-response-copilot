
import json
from types import SimpleNamespace

import pytest

from incident_copilot import investigation_graph as graph_module


def sample_state():
    return {
        "incident": {
            "title": "Payment API failure",
            "service": "payment-api",
            "description": "Repeated HTTP 500 errors",
            "severity": "High",
        },
        "current_logs": ["ERROR reason=simulated_failure"],
        "classification": {
            "classification": "simulated"
        },
        "failure_injection_detected": True,
        "retrieved_evidence": {
            "runbooks": [],
            "historical_incidents": [],
        },
    }


def mock_groq(monkeypatch, content):
    """Provide a fake Groq response without an API call."""

    mock_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        ),
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
        graph_module.os,
        "getenv",
        lambda key, default=None: (
            "fake-test-key"
            if key == "GROQ_API_KEY"
            else default
        ),
    )


def test_missing_groq_api_key(monkeypatch):
    monkeypatch.setattr(
        graph_module.os,
        "getenv",
        lambda key, default=None: None
        if key == "GROQ_API_KEY"
        else default,
    )

    with pytest.raises(
        RuntimeError,
        match="GROQ_API_KEY is missing",
    ):
        graph_module.investigate_node(sample_state())


def test_empty_groq_response(monkeypatch):
    mock_groq(monkeypatch, "")

    with pytest.raises(
        RuntimeError,
        match="Groq returned an empty response",
    ):
        graph_module.investigate_node(sample_state())


def test_invalid_groq_json(monkeypatch):
    mock_groq(monkeypatch, "This is not valid JSON")

    with pytest.raises(
        RuntimeError,
        match="Groq returned invalid JSON",
    ):
        graph_module.investigate_node(sample_state())


def test_verify_rejects_json_array():
    with pytest.raises(
        RuntimeError,
        match="must be a JSON object",
    ):
        graph_module.verify_node({
            "report": ["not", "an", "object"],
            "classification": {"classification": "unknown"},
            "failure_injection_detected": False,
            "current_logs": [],
            "retrieved_evidence": {
                "runbooks": [],
                "historical_incidents": [],
            },
        })
