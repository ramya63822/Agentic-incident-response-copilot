
from incident_copilot.document_processor import (
    load_documents,
    build_chunks,
)

documents = load_documents()
chunks = build_chunks()

print("Documents loaded:", len(documents))
print("Chunks created:", len(chunks))

for chunk in chunks:
    print("\nSource:", chunk["metadata"]["source"])
    print("Type:", chunk["metadata"]["type"])
    print("Chunk:", chunk["content"][:200])
