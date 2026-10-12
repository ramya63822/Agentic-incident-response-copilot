"""Simple, transparent log analysis utilities for the first milestone."""

from collections.abc import Iterable

ERROR_KEYWORDS = ("error", "exception", "failed", "failure", "critical", "traceback")
WARNING_KEYWORDS = ("warning", "warn", "retry", "timeout")


def analyze_log_text(log_text: str) -> dict:
    """Count log lines and return lines containing common error/warning keywords.

    This is keyword-based triage, not root-cause analysis.
    """
    lines = [line.strip() for line in log_text.splitlines() if line.strip()]
    error_lines = [
        line for line in lines
        if any(keyword in line.lower() for keyword in ERROR_KEYWORDS)
    ]
    warning_lines = [
        line for line in lines
        if any(keyword in line.lower() for keyword in WARNING_KEYWORDS)
        and line not in error_lines
    ]

    signals = []
    if error_lines:
        signals.append(f"Found {len(error_lines)} line(s) containing error-like keywords.")
    if warning_lines:
        signals.append(f"Found {len(warning_lines)} line(s) containing warning/retry/timeout keywords.")

    return {
        "total_lines": len(lines),
        "error_count": len(error_lines),
        "warning_count": len(warning_lines),
        "matching_lines": error_lines + warning_lines,
        "signals": signals,
    }


def analyze_log_lines(lines: Iterable[str]) -> dict:
    """Convenience wrapper for an iterable of log lines."""
    return analyze_log_text("\n".join(lines))
