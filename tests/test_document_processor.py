
from incident_copilot.document_processor import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_short_text_returns_one_chunk():
    text = "Payment API is working."
    assert chunk_text(text) == [text]


def test_chunks_respect_size():
    text = " ".join(["payment"] * 200)

    chunks = chunk_text(
        text,
        chunk_size=100,
        overlap=20,
    )

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_invalid_overlap_is_rejected():
    import pytest

    with pytest.raises(ValueError):
        chunk_text("sample text", chunk_size=100, overlap=100)
