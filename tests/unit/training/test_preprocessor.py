"""Unit tests for Preprocessor."""
import pytest

from backend.infrastructure.training.preprocessor import Preprocessor


class _FakeTok:
    """Byte-level fake tokenizer for tests."""
    def encode(self, text: str):
        class Enc:
            ids = list(text.encode("utf-8"))
        return Enc()


@pytest.fixture
def preprocessor():
    return Preprocessor(_FakeTok(), max_length=16, stride=8)


def test_chunks_fixed_length(preprocessor):
    texts = iter(["Hello world", "Fine-tuning is great"])
    chunks = preprocessor.process_samples(texts)
    for chunk in chunks:
        assert len(chunk) == 16


def test_pads_tail(preprocessor):
    # Single short text produces a single padded chunk
    chunks = preprocessor.process_samples(iter(["Hi"]))
    assert len(chunks) == 1
    assert len(chunks[0]) == 16
    assert chunks[0][-1] == 0  # padding token


def test_empty_input(preprocessor):
    chunks = preprocessor.process_samples(iter([]))
    assert chunks == []
