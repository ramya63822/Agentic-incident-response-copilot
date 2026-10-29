
import os
import json

from dotenv import load_dotenv
from groq import Groq

from incident_copilot.evidence_retriever import retrieve_evidence
from incident_copilot.incident_classifier import classify_incident


load_dotenv()


SYSTEM_INSTRUCTIONS = """
You are an AI Incident Response Copilot.

Your job is to investigate software incidents using:
1. Current incident logs
2. Operational runbooks
3. Historical incident records
4. Deterministic incident classification

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
- Respect the supplied deterministic incident classification.
- Do not change the classification based on assumptions.
- If the classification is simulated, explain that the errors
  were intentionally generated.
- If the classification is mixed, investigate both simulated
  and non-simulated evidence separately.
- An operational_candidate is not a confirmed production incident.
- Never claim that the root cause is confirmed without evidence.
- Use evidence labels:
  [CURRENT LOG]
  [RUNBOOK]
  [HISTORICAL INCIDENT]

Return a valid JSON object with this structure:

{
    "incident_summary": "string",
    "observed_facts": [],
    "possible_causes": [],
    "recommended_checks": [],
    "root_cause_confirmed": false,
    "limitations": []
}
"""


def detect_failure_injection(logs):
    """Detect intentional failure injection in incident logs."""

    return any(
        "reason=simulated_failure" in line.lower()
        for line in logs
    )


def investigate_incident(incident: dict) -> dict:
    """Classify, retrieve evidence and investigate using Groq."""

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

    # Preserve current incident evidence.
    current_logs = [
        str(line)
        for line in evidence_lines
        if str(line).strip()
    ]

    # Step 1: Detect intentional failure injection.
    failure_injection_detected = detect_failure_injection(
        current_logs
    )

    # Step 2: Classify the incident deterministically.
    classification = classify_incident(current_logs)

    # Step 3: Retrieve supporting contextual evidence.
    query = " ".join([
        str(title),
        str(service),
        str(description),
        " ".join(current_logs),
    ])

    retrieved = retrieve_evidence(
        query=query,
        top_k=3,
    )

    def prepare_context(items):
        return [
        {
            "source": item["source"],
            "type": item["type"],
            "content": item["content"],
            "distance": item["distance"],
            "metadata": item["metadata"],
        }
        for item in items
        ]

    runbooks = prepare_context(retrieved["runbooks"])

    historical_incidents = prepare_context(
    retrieved["historical_incidents"]
    )

    # Step 4: Prepare structured investigation input.
    investigation_input = {
        "current_incident": {
            "title": title,
            "service": service,
            "description": description,
            "severity": severity,
        },

        "incident_classification": classification,

        "failure_injection_detected": failure_injection_detected,

        "current_log_evidence": current_logs,

        "runbook_context": runbooks,

        "historical_incident_context": historical_incidents,

        "investigation_instruction": (
            "Investigate the incident using the supplied evidence. "
            "Respect the deterministic classification. "
            "For mixed incidents, distinguish simulated errors "
            "from other errors. "
            "For operational candidates, investigate possible "
            "real operational problems without assuming they "
            "are confirmed production incidents. "
            "Use runbooks and historical incidents only as "
            "contextual evidence. "
            "Do not claim a confirmed root cause without proof."
        ),
    }

    # Step 5: Call Groq.
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

    # Step 6: Validate the report.
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
    if historical_incidents and result["root_cause_confirmed"]:
        raise RuntimeError(
        "Root cause cannot be confirmed using historical "
        "incidents alone. Verify against current evidence."
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

    # Step 7: Preserve deterministic classification.
    result["incident_classification"] = classification

    result["failure_injection_detected"] = (
        failure_injection_detected
    )

    # Preserve source attribution for the dashboard.
    result["evidence_sources"] = {
        "current_logs": [
        "Current incident stored evidence"
        ] if current_logs else [],

        "runbooks": runbooks,

        "historical_incidents": historical_incidents,
    }

    result["model"] = model

    result["usage"] = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    return result
