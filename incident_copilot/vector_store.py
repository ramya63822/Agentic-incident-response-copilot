
"""Create and query the ChromaDB knowledge base."""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from incident_copilot.document_processor import build_chunks


BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

COLLECTION_NAME = "incident_knowledge"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# Load the local embedding model.
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# Create a persistent ChromaDB client.
client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)



def index_documents() -> int:
    """Rebuild the knowledge base using current document chunks."""

    chunks = build_chunks()

    # Remove old records to prevent stale chunks.
    existing = collection.get()

    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    if not chunks:
        return 0

    embeddings = embedding_model.encode(
        [chunk["content"] for chunk in chunks],
        normalize_embeddings=True,
    ).tolist()

    collection.add(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
        embeddings=embeddings,
    )

    return len(chunks)




def search_knowledge(
    query: str,
    top_k: int = 3,
    max_per_source: int = 2,
    max_distance: float = 0.75,
) -> list[dict]:
    """Retrieve relevant and diverse knowledge chunks."""

    if not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if max_per_source < 1:
        raise ValueError("max_per_source must be at least 1")

    if not 0 <= max_distance <= 2:
        raise ValueError("max_distance must be between 0 and 2")

    count = collection.count()

    if count == 0:
        return []

    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(count, max(top_k * 3, top_k)),
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    source_counts = {}

    for index, content in enumerate(results["documents"][0]):

        metadata = results["metadatas"][0][index]
        distance = results["distances"][0][index]

        if distance > max_distance:
            continue

        source = metadata["source"]

        source_counts.setdefault(source, 0)

        if source_counts[source] >= max_per_source:
            continue

        retrieved.append({
            "content": content,
            "source": source,
            "type": metadata["type"],
            "metadata": metadata,
            "distance": distance,
        })

        source_counts[source] += 1

        if len(retrieved) >= top_k:
            break

    return retrieved

