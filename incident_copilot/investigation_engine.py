
from incident_copilot.investigation_graph import investigation_graph


def investigate_incident(incident: dict) -> dict:
    """Run the incident investigation through LangGraph."""

    evidence_lines = incident.get("evidence", [])

    if isinstance(evidence_lines, str):
        evidence_lines = [evidence_lines]

    if not isinstance(evidence_lines, list):
        evidence_lines = []

    current_logs = [
        str(line)
        for line in evidence_lines
        if str(line).strip()
    ]

    initial_state = {
        "incident": incident,
        "current_logs": current_logs,
    }

    final_state = investigation_graph.invoke(initial_state)

    return final_state["report"]
