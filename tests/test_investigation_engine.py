
"""Test the Groq-powered incident investigation engine."""

import json

from incident_copilot.incident_store import list_incidents
from incident_copilot.investigation_engine import (
    investigate_incident,
)


def main():

    # Retrieve the latest actual incident from SQLite.
    incidents = list_incidents()

    if not incidents:
        print("No incidents found in SQLite.")
        return

    latest_incident = incidents[0]

    sample_incident = {
        "title": latest_incident["title"],
        "service": latest_incident["service"],
        "severity": latest_incident["severity"],
        "description": (
            "Investigate the detected incident using "
            "current logs, runbooks, and historical evidence."
        ),
        "evidence": latest_incident["evidence"],
    }

    print("Starting AI incident investigation...")
    print("Incident ID:", latest_incident["id"])
    print("Service:", latest_incident["service"])

    report = investigate_incident(sample_incident)

    print("\n========== AI INVESTIGATION REPORT ==========")

    print(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
