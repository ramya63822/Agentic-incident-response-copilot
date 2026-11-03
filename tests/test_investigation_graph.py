
import pytest

from incident_copilot import investigation_graph as graph_module


def test_classify_simulated_incident():
    result = graph_module.classify_node({
        "current_logs": [
            "ERROR status=500 reason=simulated_failure"
        ]
    })

    assert result["classification"]["classification"] == "simulated"
    assert result["failure_injection_detected"] is True


def test_classify_operational_candidate():
    result = graph_module.classify_node({
        "current_logs": [
            "ERROR database connection timeout"
        ]
    })

    assert (
        result["classification"]["classification"]
        == "operational_candidate"
    )


def test_classify_mixed_incident():
    result = graph_module.classify_node({
        "current_logs": [
            "ERROR reason=simulated_failure",
            "ERROR database connection timeout",
        ]
    })

    assert result["classification"]["classification"] == "mixed"


def test_verify_rejects_missing_fields():
    with pytest.raises(RuntimeError, match="Missing report fields"):
        graph_module.verify_node({
            "report": {},
            "classification": {"classification": "unknown"},
            "failure_injection_detected": False,
            "current_logs": [],
            "retrieved_evidence": {
                "runbooks": [],
                "historical_incidents": [],
            },
        })


def test_verify_rejects_invalid_root_cause_type():
    report = {
        "incident_summary": "Test incident",
        "observed_facts": [],
        "possible_causes": [],
        "recommended_checks": [],
        "root_cause_confirmed": "false",
        "limitations": [],
    }

    with pytest.raises(
        RuntimeError,
        match="root_cause_confirmed must be a boolean",
    ):
        graph_module.verify_node({
            "report": report,
            "classification": {"classification": "simulated"},
            "failure_injection_detected": True,
            "current_logs": [],
            "retrieved_evidence": {
                "runbooks": [],
                "historical_incidents": [],
            },
        })


def test_verify_normalizes_string_limitations():
    report = {
        "incident_summary": "Simulated payment failure",
        "observed_facts": [],
        "possible_causes": [],
        "recommended_checks": [],
        "root_cause_confirmed": False,
        "limitations": "No production metrics available.",
    }

    result = graph_module.verify_node({
        "report": report,
        "classification": {"classification": "simulated"},
        "failure_injection_detected": True,
        "current_logs": ["reason=simulated_failure"],
        "retrieved_evidence": {
            "runbooks": [],
            "historical_incidents": [],
        },
    })

    assert result["report"]["limitations"] == [
        "No production metrics available."
    ]


def test_verify_rejects_root_cause_based_on_historical_context():
    report = {
        "incident_summary": "Payment failure",
        "observed_facts": [],
        "possible_causes": [],
        "recommended_checks": [],
        "root_cause_confirmed": True,
        "limitations": [],
    }

    with pytest.raises(
        RuntimeError,
        match="historical incidents alone",
    ):
        graph_module.verify_node({
            "report": report,
            "classification": {
                "classification": "operational_candidate"
            },
            "failure_injection_detected": False,
            "current_logs": ["HTTP 500"],
            "retrieved_evidence": {
                "runbooks": [],
                "historical_incidents": [
                    {"source": "historical_incidents.json"}
                ],
            },
        })
