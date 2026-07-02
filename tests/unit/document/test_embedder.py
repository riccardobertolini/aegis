"""Unit tests — FallbackHashEmbedder (no ML deps required)."""
from backend.infrastructure.document.embedder import FallbackHashEmbedder


def test_embed_returns_correct_count():
    e = FallbackHashEmbedder()
    vecs = e.embed(["hello", "world"])
    assert len(vecs) == 2


def test_embed_dimension():
    e = FallbackHashEmbedder()
    vecs = e.embed(["test"])
    assert len(vecs[0]) == e.dimension() == 64


def test_embed_deterministic():
    e = FallbackHashEmbedder()
    a = e.embed(["deterministic text"])
    b = e.embed(["deterministic text"])
    assert a == b


def test_embed_different_texts_differ():
    e = FallbackHashEmbedder()
    a = e.embed(["text A"])
    b = e.embed(["text B"])
    assert a != b


def test_embed_values_in_range():
    e = FallbackHashEmbedder()
    vecs = e.embed(["range check"])
    for v in vecs[0]:
        assert 0.0 <= v <= 1.0
