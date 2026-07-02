"""Unit tests for TextChunker."""
from __future__ import annotations

import pytest

from backend.infrastructure.rag.chunker import TextChunker


@pytest.fixture()
def chunker() -> TextChunker:
    return TextChunker(chunk_size=128, chunk_overlap=16, min_chunk_len=8)


def test_chunk_text_basic(chunker: TextChunker):
    text = "This is sentence one. This is sentence two. This is sentence three."
    chunks = chunker.chunk_text("doc1", text)
    assert len(chunks) >= 1
    for c in chunks:
        assert len(c.text) >= 8
        assert c.document_id == "doc1"


def test_chunk_indices_sequential(chunker: TextChunker):
    text = ("Sentence number {i}. " * 30).format(i=0)
    chunks = chunker.chunk_text("doc2", text)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_document_joins_blocks(chunker: TextChunker):
    blocks = ["First block content here.", "Second block content here."]
    chunks = chunker.chunk_document("doc3", blocks)
    full = " ".join(c.text for c in chunks)
    assert "First block" in full
    assert "Second block" in full


def test_chunk_overlap_invalid_raises():
    with pytest.raises(ValueError):
        TextChunker(chunk_size=64, chunk_overlap=64)


def test_empty_text_returns_no_chunks(chunker: TextChunker):
    chunks = chunker.chunk_text("doc4", "")
    assert chunks == []


def test_very_long_sentence_hard_split():
    c = TextChunker(chunk_size=32, chunk_overlap=4, min_chunk_len=4)
    long = "word " * 100  # no punctuation, one long block
    chunks = c.chunk_text("doc5", long)
    assert len(chunks) >= 2
    for ch in chunks:
        assert len(ch.text) <= 36  # chunk_size + small slack
