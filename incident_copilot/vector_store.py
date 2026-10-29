
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
    """Generate embeddings and index knowledge chunks."""
    chunks = build_chunks()

    if not chunks:
        return 0

    embeddings = embedding_model.encode(
        [chunk["content"] for chunk in chunks],
        normalize_embeddings=True,
    ).tolist()

    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
        embeddings=embeddings,
    )

    return len(chunks)


def search_knowledge(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """Retrieve relevant knowledge using semantic similarity."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if collection.count() == 0:
        return []

    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []

    for index, content in enumerate(results["documents"][0]):
        retrieved.append({
            "content": content,
            "source": results["metadatas"][0][index]["source"],
            "type": results["metadatas"][0][index]["type"],
            "metadata": results["metadatas"][0][index],
            "distance": results["distances"][0][index],
        })

    return retrieved
