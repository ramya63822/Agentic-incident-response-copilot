
import os
import json
from typing import TypedDict, Any

from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, START, END
from rich.diagnose import report

from incident_copilot.incident_classifier import classify_incident
from incident_copilot.evidence_retriever import retrieve_evidence


load_dotenv()


SYSTEM_INSTRUCTIONS = """
You are an AI Incident Response Copilot.

Investigate incidents using current logs, runbooks,
historical incidents, and deterministic classification.

Rules:
- observed_facts must always be a JSON array.
- possible_causes must always be a JSON array.
- recommended_checks must always be a JSON array.
- limitations must always be a JSON array.
- Even when there is only one item, return an array.
- Return an empty array when there are no items.
- Separate observed facts from possible causes.
- Current logs are primary evidence.
- Runbooks provide guidance, not proof.
- Historical incidents provide context, not proof.
- Identify missing evidence.
- Respect the deterministic classification.
- Treat reason=simulated_failure as intentional failure injection.
- Never recommend automatic production changes.
- Never confirm a root cause without direct evidence.

Return valid JSON with:
incident_summary, observed_facts, possible_causes,
recommended_checks, root_cause_confirmed, limitations.
"""


class InvestigationState(TypedDict, total=False):
    incident: dict
    current_logs: list[str]
    failure_injection_detected: bool
    classification: dict
    query: str
    retrieved_evidence: dict
    investigation_input: dict
    report: dict
    error: str


def classify_node(state: InvestigationState) -> dict:
    """Classify current incident evidence."""

    logs = state["current_logs"]

    classification = classify_incident(logs)

    failure_injection = any(
        "reason=simulated_failure" in line.lower()
        for line in logs
    )

    return {
        "classification": classification,
        "failure_injection_detected": failure_injection,
    }


def retrieve_node(state: InvestigationState) -> dict:
    """Retrieve runbooks and historical incidents."""

    incident = state["incident"]

    query = " ".join([
        str(incident.get("title", "")),
        str(incident.get("service", "")),
        str(incident.get("description", "")),
        " ".join(state["current_logs"]),
    ])

    evidence = retrieve_evidence(query=query, top_k=3)

    return {
        "query": query,
        "retrieved_evidence": evidence,
    }


def investigate_node(state: InvestigationState) -> dict:
    """Investigate using Groq and retrieved evidence."""

    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing.")

    incident = state["incident"]
    retrieved = state["retrieved_evidence"]

    investigation_input = {
        "current_incident": {
            "title": incident.get("title", "Untitled incident"),
            "service": incident.get("service", "Unknown service"),
            "description": incident.get("description", ""),
            "severity": incident.get("severity", "Unknown"),
        },
        "incident_classification": state["classification"],
        "failure_injection_detected": state[
            "failure_injection_detected"
        ],
        "current_log_evidence": state["current_logs"],
        "runbook_context": retrieved["runbooks"],
        "historical_incident_context": retrieved[
            "historical_incidents"
        ],
        "investigation_instruction": (
            "Respect the deterministic classification. "
            "Distinguish simulated and non-simulated evidence. "
            "Use historical incidents only as context. "
            "Do not confirm a root cause without proof."
        ),
    }

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {
                "role": "user",
                "content": (
                    "Investigate this incident and return JSON:\n"
                    + json.dumps(
                        investigation_input,
                        ensure_ascii=False,
                    )
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    response_text = response.choices[0].message.content

    if not response_text:
        raise RuntimeError("Groq returned an empty response.")

    try:
        report = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Groq returned invalid JSON.") from exc

    usage = response.usage

    report["model"] = model
    report["usage"] = {
        "prompt_tokens": usage.prompt_tokens if usage else 0,
        "completion_tokens": usage.completion_tokens if usage else 0,
        "total_tokens": usage.total_tokens if usage else 0,
    }

    return {
        "report": report,
        "investigation_input": investigation_input,
    }


def verify_node(state: InvestigationState) -> dict:
    """Validate the report and preserve deterministic evidence."""

    report = state["report"]

    if not isinstance(report, dict):
        raise RuntimeError(
            "Groq investigation report must be a JSON object."
        )

    required_keys = {
        "incident_summary",
        "observed_facts",
        "possible_causes",
        "recommended_checks",
        "root_cause_confirmed",
        "limitations",
    }

    missing = required_keys - report.keys()

    if missing:
        raise RuntimeError(
            f"Missing report fields: {sorted(missing)}"
        )

    if not isinstance(report["root_cause_confirmed"], bool):
        raise RuntimeError(
            "root_cause_confirmed must be a boolean."
        )

    for field in [
    "observed_facts",
    "possible_causes",
    "recommended_checks",
    "limitations",
    ]:
        value = report[field]

    # Normalize a single string into a one-item list.
        if isinstance(value, str):
            report[field] = [value]

        elif not isinstance(value, list):
            raise RuntimeError(
                f"{field} must be a list or string. "
                f"Received: {repr(value)}"
            )
    retrieved = state["retrieved_evidence"]

    if (
        retrieved["historical_incidents"]
        and report["root_cause_confirmed"]
    ):
        raise RuntimeError(
            "Root cause cannot be confirmed using historical "
            "incidents alone. Verify against current evidence."
        )

    report["incident_classification"] = state["classification"]
    report["failure_injection_detected"] = state[
        "failure_injection_detected"
    ]

    report["evidence_sources"] = {
        "current_logs": (
            ["Current incident stored evidence"]
            if state["current_logs"] else []
        ),
        "runbooks": retrieved["runbooks"],
        "historical_incidents": retrieved[
            "historical_incidents"
        ],
    }

    return {"report": report}


def build_investigation_graph():
    """Build and compile the incident investigation graph."""

    workflow = StateGraph(InvestigationState)

    workflow.add_node("classify", classify_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("investigate", investigate_node)
    workflow.add_node("verify", verify_node)

    workflow.add_edge(START, "classify")
    workflow.add_edge("classify", "retrieve")
    workflow.add_edge("retrieve", "investigate")
    workflow.add_edge("investigate", "verify")
    workflow.add_edge("verify", END)

    return workflow.compile()


investigation_graph = build_investigation_graph()
