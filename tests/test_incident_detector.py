
from incident_copilot.incident_detector import detect_incident


def test_detects_repeated_errors_within_window():
    logs = """\
2026-10-27T10:00:01Z ERROR payment-service HTTP 500
2026-10-27T10:00:20Z ERROR payment-service HTTP 500
2026-10-27T10:00:45Z ERROR payment-service HTTP 500
"""

    result = detect_incident(logs)

    assert result is not None
    assert result["service"] == "payment-service"
    assert result["severity"] == "High"
    assert result["error_count"] == 3
    assert len(result["evidence"]) == 3


def test_does_not_detect_errors_outside_window():
    logs = """\
2026-10-27T10:00:00Z ERROR payment-service HTTP 500
2026-10-27T10:01:10Z ERROR payment-service HTTP 500
2026-10-27T10:02:20Z ERROR payment-service HTTP 500
"""

    assert detect_incident(logs) is None


def test_critical_error_creates_critical_incident():
    logs = """\
2026-10-27T10:00:01Z ERROR payment-service HTTP 500
2026-10-27T10:00:10Z CRITICAL payment-service database unavailable
2026-10-27T10:00:20Z ERROR payment-service HTTP 500
"""

    result = detect_incident(logs)

    assert result is not None
    assert result["severity"] == "Critical"


def test_ignores_malformed_log_lines():
    logs = """\
This is not a valid timestamped log
2026-10-27T10:00:01Z INFO payment-service started
"""

    assert detect_incident(logs) is None


def test_rejects_invalid_threshold():
    try:
        detect_incident("some logs", error_threshold=0)
        assert False, "Expected ValueError"
    except ValueError:
        pass
