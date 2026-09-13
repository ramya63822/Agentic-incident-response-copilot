
"""Simulate incoming monitoring logs for the payment service."""

from incident_copilot.incident_detector import detect_incident


SAMPLE_ALERT_LOGS = """\
2026-10-27T10:15:18Z ERROR payment-api request failed status=500 route=/charge request_id=req-1001
2026-10-27T10:15:19Z ERROR payment-api database connection timeout request_id=req-1002
2026-10-27T10:15:26Z ERROR payment-api request failed status=500 route=/charge request_id=req-1003
"""


def check_for_incident(log_text: str = SAMPLE_ALERT_LOGS) -> dict | None:
    """Check a batch of logs and return a detected incident, if any."""
    return detect_incident(
        log_text,
        error_threshold=3,
        window_seconds=60,
    )
