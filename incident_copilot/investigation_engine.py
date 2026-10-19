
import os
import json

from dotenv import load_dotenv
from groq import Groq

from incident_copilot.evidence_retriever import retrieve_evidence


load_dotenv()


SYSTEM_INSTRUCTIONS = """
You are an AI Incident Response Copilot.

Your job is to investigate software incidents using:
1. Current incident logs
2. Operational runbooks
3. Historical incident records

IMPORTANT RULES:

- Separate observed facts from possible causes.
- Never claim a root cause is confirmed without direct evidence.
- Current logs are the primary evidence for the active incident.
- Runbooks provide operational guidance, not proof of a cause.
- Historical incidents provide context, not proof that the same
  cause occurred again.
- Clearly identify missing evidence.
- Recommend practical investigation steps.
- Do not recommend automatic production changes.
- Do not recommend restarting services, changing configurations,
  or rolling back deployments automatically.
- Treat reason=simulated_failure as intentional failure injection.
- If failure injection is detected, explicitly mention it.
- Do not mistake intentional failure injection for an independently
  confirmed production root cause.
- Use evidence labels:
  [CURRENT LOG]
  [RUNBOOK]
  [HISTORICAL INCIDENT]

Return a valid JSON object with this structure:

{
    "incident_summary": "string",
    "observed_facts": [],
    "possible_causes": [
        {
            "hypothesis": "string",
            "supporting_evidence": [],
            "missing_evidence": [],
            "confidence": "Low/Medium/High"
        }
    ],
    "recommended_checks": [],
    "root_cause_confirmed": false,
    "limitations": []
}
"""


def detect_failure_injection(logs):
    """Detect intentional failure injection in incident logs."""

    return any(
        "reason=simulated_failure" in line
        for line in logs
    )


def investigate_incident(incident: dict) -> dict:
    """Retrieve evidence and investigate the incident using Groq."""

    api_key = os.getenv("GROQ_API_KEY")

    model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b",
    )

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Check your .env file."
        )

    title = incident.get("title", "Untitled incident")
    service = incident.get("service", "Unknown service")
    description = incident.get("description", "")
    severity = incident.get("severity", "Unknown")

    evidence_lines = incident.get("evidence", [])

    if isinstance(evidence_lines, str):
        evidence_lines = [evidence_lines]

    if not isinstance(evidence_lines, list):
        evidence_lines = []

    # Keep current incident evidence separate.
    current_logs = [
        str(line)
        for line in evidence_lines
        if str(line).strip()
    ]

    # Detect intentional failure injection.
    failure_injection_detected = detect_failure_injection(
        current_logs
    )

    query = " ".join([
        str(title),
        str(service),
        str(description),
        " ".join(current_logs),
    ])

    # Retrieve contextual evidence.
    retrieved = retrieve_evidence(
        query=query,
        top_k=3,
    )

    runbooks = [
        {
            "source": item["source"],
            "content": item["content"],
        }
        for item in retrieved["runbooks"]
    ]

    historical_incidents = [
        {
            "source": item["source"],
            "content": item["content"],
        }
        for item in retrieved["historical_incidents"]
    ]

    # Prepare evidence for the AI investigation.
    investigation_input = {
        "current_incident": {
            "title": title,
            "service": service,
            "description": description,
            "severity": severity,
        },

        "current_log_evidence": current_logs,

        "failure_injection_detected": failure_injection_detected,

        "runbook_context": runbooks,

        "historical_incident_context": historical_incidents,

        "investigation_instruction": (
            "Investigate the current incident. "
            "Compare hypotheses using current logs. "
            "Use runbooks and historical incidents only "
            "as contextual evidence. "
            "If failure_injection_detected is true, explicitly "
            "identify that intentional failure injection was detected. "
            "Do not mistake it for an independently confirmed "
            "production root cause."
        ),
    }

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTIONS,
            },
            {
                "role": "user",
                "content": (
                    "Investigate this incident and return "
                    "the requested JSON report.\n\n"
                    + json.dumps(
                        investigation_input,
                        ensure_ascii=False,
                    )
                ),
            },
        ],
        response_format={
            "type": "json_object",
        },
        temperature=0.2,
    )

    response_text = response.choices[0].message.content

    if not response_text:
        raise RuntimeError(
            "Groq returned an empty investigation response."
        )

    try:
        result = json.loads(response_text)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Groq did not return valid JSON."
        ) from exc

    # Validate the required report structure.
    required_keys = {
        "incident_summary",
        "observed_facts",
        "possible_causes",
        "recommended_checks",
        "root_cause_confirmed",
        "limitations",
    }

    missing_keys = required_keys - result.keys()

    if missing_keys:
        raise RuntimeError(
            f"Missing report fields: {sorted(missing_keys)}"
        )

    if not isinstance(result["root_cause_confirmed"], bool):
        raise RuntimeError(
            "root_cause_confirmed must be a boolean."
        )

    for field in [
        "observed_facts",
        "possible_causes",
        "recommended_checks",
        "limitations",
    ]:
        if not isinstance(result[field], list):
            raise RuntimeError(
                f"{field} must be a list."
            )

    # Preserve source attribution for the dashboard.
    result["evidence_sources"] = {
        "current_logs": [
            "Current incident stored evidence"
        ] if current_logs else [],

        "runbooks": [
            item["source"] for item in runbooks
        ],

        "historical_incidents": [
            item["source"]
            for item in historical_incidents
        ],
    }

    result["failure_injection_detected"] = (
        failure_injection_detected
    )

    result["model"] = model

    result["usage"] = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    return result
