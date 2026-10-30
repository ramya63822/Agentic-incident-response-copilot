
from incident_copilot.document_processor import (
    load_documents,
    build_chunks,
)


def test_documents_are_loaded():
    documents = load_documents()

    assert len(documents) > 0


def test_chunks_are_created():
    chunks = build_chunks()

    assert len(chunks) > 0

    for chunk in chunks:
        assert "content" in chunk
        assert "metadata" in chunk
        assert chunk["content"].strip()
