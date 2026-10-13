
"""Rule-based automatic incident detection from timestamped logs."""

import re
from datetime import datetime, timedelta, timezone


LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\S+)\s+"
    r"(?P<level>[A-Z]+)\s+"
    r"(?P<service>\S+)\s+"
    r"(?P<message>.*)$"
)

ERROR_LEVELS = {"ERROR", "CRITICAL", "FATAL"}


def detect_incident(
    log_text: str,
    error_threshold: int = 3,
    window_seconds: int = 60,
) -> dict | None:
    """Return an incident when enough errors occur within a time window.

    Lines that do not match the expected timestamped format are ignored.
    Returns None when no incident threshold is reached.
    """
    if error_threshold < 1:
        raise ValueError("error_threshold must be at least 1")
    if window_seconds < 1:
        raise ValueError("window_seconds must be at least 1")

    errors = []

    for line in log_text.splitlines():
        line = line.strip()
        match = LOG_PATTERN.match(line)

        if not match:
            continue

        if match.group("level") not in ERROR_LEVELS:
            continue

        try:
            timestamp = datetime.fromisoformat(
                match.group("timestamp").replace("Z", "+00:00")
            )
        except ValueError:
            continue

        # Treat timestamps without a timezone as UTC.
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        errors.append({
            "timestamp": timestamp,
            "level": match.group("level"),
            "service": match.group("service"),
            "line": line,
        })

    errors.sort(key=lambda item: item["timestamp"])
    left = 0

    for right, current in enumerate(errors):
        while (
            current["timestamp"] - errors[left]["timestamp"]
            > timedelta(seconds=window_seconds)
        ):
            left += 1

        window_errors = errors[left:right + 1]

        if len(window_errors) >= error_threshold:
            services = sorted({
                item["service"] for item in window_errors
            })
            service = services[0] if len(services) == 1 else "multiple services"

            critical_found = any(
                item["level"] in {"CRITICAL", "FATAL"}
                for item in window_errors
            )

            return {
                "title": f"Repeated errors detected in {service}",
                "severity": "Critical" if critical_found else "High",
                "service": service,
                "error_count": len(window_errors),
                "window_seconds": window_seconds,
                "description": (
                    f"Detected {len(window_errors)} error log entries "
                    f"within {window_seconds} seconds."
                ),
                "evidence": [
                    item["line"] for item in window_errors
                ],
                "first_seen": window_errors[0]["timestamp"].isoformat(),
                "last_seen": current["timestamp"].isoformat(),
            }

    return None
