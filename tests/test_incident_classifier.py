
from incident_copilot.incident_classifier import classify_incident


def test_simulated_incident_classification():
    logs = [
        "ERROR payment-api reason=simulated_failure",
        "ERROR payment-api reason=simulated_failure",
    ]

    result = classify_incident(logs)

    assert result is not None
    assert isinstance(result, dict)


def test_unknown_incident_classification():
    result = classify_incident([])

    assert result is not None
    assert isinstance(result, dict)
