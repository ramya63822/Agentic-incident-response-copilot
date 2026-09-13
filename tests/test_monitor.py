
from incident_copilot.monitor import (
    SAMPLE_ALERT_LOGS,
    check_for_incident,
)


def test_monitor_detects_payment_incident():
    incident = check_for_incident()

    assert incident is not None
    assert incident["service"] == "payment-api"
    assert incident["error_count"] == 3


def test_monitor_returns_none_when_no_errors():
    logs = """\
2026-10-27T10:15:18Z INFO payment-api request completed
2026-10-27T10:15:19Z INFO payment-api request completed
"""

    assert check_for_incident(logs) is None


def test_monitor_uses_actual_supplied_logs():
    logs = """\
2026-10-27T10:15:18Z ERROR inventory-api request failed
2026-10-27T10:15:19Z ERROR inventory-api request failed
2026-10-27T10:15:20Z ERROR inventory-api request failed
"""

    incident = check_for_incident(logs)

    assert incident is not None
    assert incident["service"] == "inventory-api"
