
"""Load and chunk runbooks and historical incidents for RAG."""

import hashlib
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

RUNBOOK_DIR = BASE_DIR / "data" / "runbooks"
HISTORICAL_INCIDENTS_FILE = (
    BASE_DIR / "data" / "incidents" / "historical_incidents.json"
)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80


def load_documents() -> list[dict]:
    """Load runbooks and historical incidents."""
    documents = []

    # Load Markdown runbooks.
    if RUNBOOK_DIR.exists():
        for path in RUNBOOK_DIR.glob("*.md"):
            content = path.read_text(encoding="utf-8").strip()

            if content:
                documents.append({
                    "source": path.name,
                    "content": content,
                    "type": "runbook",
                })

    # Load historical incident records.
    if HISTORICAL_INCIDENTS_FILE.exists():
        with HISTORICAL_INCIDENTS_FILE.open(
            "r", encoding="utf-8"
        ) as file:
            historical_data = json.load(file)

        if isinstance(historical_data, dict):
            historical_data = historical_data.get("incidents", [])

        if not isinstance(historical_data, list):
            raise ValueError("Historical incidents must be a list")

        for incident in historical_data:
            if not isinstance(incident, dict):
                continue

            content = "\n".join(
                f"{key}: {json.dumps(value, ensure_ascii=False)}"
                for key, value in incident.items()
            )

            documents.append({
                "source": "historical_incidents.json",
                "content": content,
                "type": "historical_incident",
                "incident_id": str(
                    incident.get("incident_id", "unknown")
                ),
            })

    return documents



def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks using natural boundaries."""

    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size"
        )

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            # Prefer paragraph boundary.
            boundary = text.rfind("\n\n", start, end)

            # Otherwise prefer sentence boundary.
            if boundary == -1:
                boundary = max(
                    text.rfind(". ", start, end),
                    text.rfind("? ", start, end),
                    text.rfind("! ", start, end),
                )

            # Otherwise prefer word boundary.
            if boundary == -1:
                boundary = text.rfind(" ", start, end)

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        # Calculate overlap and align the next start to a word.
        next_start = max(start + 1, end - overlap)

        while next_start < end and text[next_start].isalnum():
            next_start += 1

        start = next_start

    return chunks

def build_chunks() -> list[dict]:
    """Convert loaded documents into chunks with stable IDs."""
    chunks = []

    for document in load_documents():
        for index, content in enumerate(
            chunk_text(document["content"])
        ):
            identity = (
                f'{document["source"]}:'
                f'{document.get("incident_id", "")}:'
                f'{index}:'
                f'{content}'
            )

            chunk_id = hashlib.sha256(
                identity.encode("utf-8")
            ).hexdigest()

            metadata = {
                "source": document["source"],
                "type": document["type"],
                "chunk_index": index,
            }

            if "incident_id" in document:
                metadata["incident_id"] = document["incident_id"]

            chunks.append({
                "id": chunk_id,
                "content": content,
                "metadata": metadata,
            })

    return chunks
