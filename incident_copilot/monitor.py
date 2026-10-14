
"""Read Payment API logs and detect recent incidents."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from incident_copilot.incident_detector import detect_incident

BASE_DIR = Path(__file__).resolve().parent.parent
PAYMENT_LOG_FILE = BASE_DIR / "data" / "logs" / "payment_api.log"

SAMPLE_ALERT_LOGS = """\
2026-10-27T10:15:18Z ERROR payment-api request failed status=500 route=/charge request_id=req-1001
2026-10-27T10:15:19Z ERROR payment-api database connection timeout request_id=req-1002
2026-10-27T10:15:26Z ERROR payment-api request failed status=500 route=/charge request_id=req-1003
"""


def load_payment_api_logs() -> str:
    """Read logs written by the simulated Payment API."""
    if not PAYMENT_LOG_FILE.exists():
        return ""

    return PAYMENT_LOG_FILE.read_text(encoding="utf-8")


def check_for_incident(
    log_text: str = SAMPLE_ALERT_LOGS,
    error_threshold: int = 3,
    window_seconds: int = 60,
    lookback_seconds: int = 60,
) -> dict | None:
    """Detect repeated errors within a recent time window."""
    if lookback_seconds < 1:
        raise ValueError("lookback_seconds must be at least 1")

    cutoff = datetime.now(timezone.utc) - timedelta(
        seconds=lookback_seconds
    )

    recent_lines = []

    for line in log_text.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            continue

        try:
            timestamp = datetime.fromisoformat(
                parts[0].replace("Z", "+00:00")
            )
        except ValueError:
            continue

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        if timestamp >= cutoff:
            recent_lines.append(line)

    return detect_incident(
        "\n".join(recent_lines),
        error_threshold=error_threshold,
        window_seconds=window_seconds,
    )
