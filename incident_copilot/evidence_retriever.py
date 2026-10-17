
"""Retrieve relevant runbooks and historical incidents."""

import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

RUNBOOK_DIR = BASE_DIR / "data" / "runbooks"
HISTORICAL_INCIDENTS_FILE = (
    BASE_DIR / "data" / "incidents" / "historical_incidents.json"
)


def tokenize(text: str) -> set[str]:
    """Convert text into lowercase searchable keywords."""
    return set(re.findall(r"\b[a-z0-9_-]+\b", text.lower()))


def calculate_relevance(
    query: str,
    document: str,
) -> int:
    """Score a document based on keyword overlap with the query."""
    query_words = tokenize(query)
    document_words = tokenize(document)

    # Ignore very common words that add little search value.
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were",
        "in", "on", "at", "to", "of", "for", "and",
        "or", "with", "this", "that", "it", "from",
    }

    query_words -= stop_words
    document_words -= stop_words

    return len(query_words & document_words)


def retrieve_runbooks(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """Return the most relevant runbook files."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    results = []

    if not RUNBOOK_DIR.exists():
        return results

    for path in RUNBOOK_DIR.glob("*.md"):
        content = path.read_text(encoding="utf-8")
        score = calculate_relevance(query, content)

        if score > 0:
            results.append({
                "source": path.name,
                "content": content,
                "relevance_score": score,
                "type": "runbook",
            })

    results.sort(
        key=lambda item: item["relevance_score"],
        reverse=True,
    )

    return results[:top_k]


def retrieve_historical_incidents(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """Return historical incidents relevant to a query."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if not HISTORICAL_INCIDENTS_FILE.exists():
        return []

    with HISTORICAL_INCIDENTS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        historical_data = json.load(file)

    # Accept either a JSON list or a dictionary containing a list.
    if isinstance(historical_data, dict):
        historical_data = historical_data.get(
            "incidents", []
        )

    if not isinstance(historical_data, list):
        raise ValueError(
            "Historical incidents JSON must contain a list "
            "or an 'incidents' list."
        )

    results = []

    for incident in historical_data:
        if not isinstance(incident, dict):
            continue

        searchable_text = json.dumps(
            incident,
            ensure_ascii=False,
        )

        score = calculate_relevance(
            query,
            searchable_text,
        )

        if score > 0:
            results.append({
                "source": "historical_incidents.json",
                "content": incident,
                "relevance_score": score,
                "type": "historical_incident",
            })

    results.sort(
        key=lambda item: item["relevance_score"],
        reverse=True,
    )

    return results[:top_k]


def retrieve_evidence(
    query: str,
    top_k: int = 3,
) -> dict:
    """Retrieve relevant operational and historical evidence."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    return {
        "query": query,
        "runbooks": retrieve_runbooks(query, top_k),
        "historical_incidents": retrieve_historical_incidents(
            query,
            top_k,
        ),
    }
