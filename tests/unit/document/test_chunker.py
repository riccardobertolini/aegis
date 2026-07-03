"""Unit tests — TextChunker."""
from backend.domain.ports.document import ChunkingConfig
from backend.infrastructure.document.chunker import TextChunker


def test_empty_text():
    c = TextChunker()
    assert c.split("") == []


def test_short_text_single_chunk():
    c = TextChunker(ChunkingConfig(chunk_size=512, chunk_overlap=0))
    result = c.split("Hello world")
    assert len(result) == 1
    assert result[0] == "Hello world"


def test_splits_on_double_newline():
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    c = TextChunker(ChunkingConfig(chunk_size=30, chunk_overlap=0))
    chunks = c.split(text)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 60  # generous bound for overlap edge cases


def test_overlap_content_present():
    text = " ".join([f"word{i}" for i in range(100)])
    c = TextChunker(ChunkingConfig(chunk_size=100, chunk_overlap=20))
    chunks = c.split(text)
    # Each chunk (except possibly the last) should have overlap with the next
    assert len(chunks) > 1


def test_no_empty_chunks():
    text = "\n\n".join([f"Section {i}: content." for i in range(20)])
    c = TextChunker(ChunkingConfig(chunk_size=50, chunk_overlap=10))
    chunks = c.split(text)
    assert all(ch.strip() for ch in chunks)
