
"""Test the Groq-powered incident investigation engine."""

import json

from incident_copilot.investigation_engine import (
    investigate_incident,
)


def main():

    sample_incident = {
        "title": "Payment API returning HTTP 500 errors",
        "service": "payment-api",
        "severity": "High",
        "description": (
            "Repeated payment failures were detected. "
            "Investigate possible database connection problems."
        ),
        "evidence": [
            (
                "ERROR payment-api request failed "
                "status=500 route=/payments"
            ),
            (
                "ERROR payment-api database connection timeout"
            ),
            (
                "ERROR payment-api request failed "
                "status=500 route=/payments request_id=req-1003"
            ),
        ],
    }

    print("Starting AI incident investigation...")

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
