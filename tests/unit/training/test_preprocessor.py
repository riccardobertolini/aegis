"""Unit tests — TextPreprocessor."""
import pytest

from backend.infrastructure.training.preprocessor import TextPreprocessor


class _FakeTok:
    class _Enc:
        def __init__(self, ids): self.ids = ids
    def encode(self, text: str):
        return self._Enc(list(text.encode("utf-8")))


def test_tokenize_short(tmp_path):
    pp = TextPreprocessor(_FakeTok(), max_seq_len=512)
    result = pp.tokenize(["hello world"])
    assert len(result) == 1
    assert result[0] == list("hello world".encode("utf-8"))


def test_tokenize_long_chunked():
    pp = TextPreprocessor(_FakeTok(), max_seq_len=10)
    text = "a" * 25
    seqs = pp.tokenize([text])
    assert len(seqs) > 1
    for s in seqs:
        assert len(s) <= 10


def test_make_batches():
    pp = TextPreprocessor(_FakeTok(), max_seq_len=512)
    seqs = [list(range(i, i + 5)) for i in range(20)]
    batches = list(pp.make_batches(seqs, batch_size=4))
    assert len(batches) == 5
    assert all(len(b) <= 4 for b in batches)
