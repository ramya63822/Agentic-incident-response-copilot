
from incident_copilot.vector_store import (
    index_documents,
    collection,
)

print("Rebuilding knowledge base...")

indexed_count = index_documents()

print("Chunks indexed:", indexed_count)
print("Total chunks in ChromaDB:", collection.count())

print("Knowledge base rebuild completed.")
