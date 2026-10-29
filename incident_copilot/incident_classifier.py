
"""Classify incidents using deterministic log evidence."""

from enum import Enum


class IncidentType(str, Enum):
    SIMULATED = "simulated"
    OPERATIONAL_CANDIDATE = "operational_candidate"
    MIXED = "mixed"
    UNKNOWN = "unknown"


def classify_incident(logs: list[str]) -> dict:
    """
    Classify an incident using its current log evidence.

    A missing simulation marker does not prove that
    an incident is a genuine production incident.
    """

    if not logs:
        return {
            "classification": IncidentType.UNKNOWN.value,
            "simulated_error_count": 0,
            "other_error_count": 0,
            "explanation": "No log evidence available.",
        }

    simulated_logs = []
    other_logs = []

    for line in logs:
        normalized_line = str(line).lower()

        if "reason=simulated_failure" in normalized_line:
            simulated_logs.append(line)
        else:
            other_logs.append(line)

    simulated_count = len(simulated_logs)
    other_count = len(other_logs)

    if simulated_count > 0 and other_count > 0:
        classification = IncidentType.MIXED
        explanation = (
            "Both intentional simulated failures and "
            "other log evidence were detected."
        )

    elif simulated_count > 0:
        classification = IncidentType.SIMULATED
        explanation = (
            "All supplied evidence contains the "
            "intentional simulated failure marker."
        )

    elif other_count > 0:
        classification = IncidentType.OPERATIONAL_CANDIDATE
        explanation = (
            "No known simulation marker was found. "
            "Further investigation is required."
        )

    else:
        classification = IncidentType.UNKNOWN
        explanation = "Unable to classify the incident."

    return {
        "classification": classification.value,
        "simulated_error_count": simulated_count,
        "other_error_count": other_count,
        "explanation": explanation,
    }
