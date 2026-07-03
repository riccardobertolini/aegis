"""Unit tests for the stub inference backend."""

from backend.infrastructure.adapters.inference._stub_backend import StubModel, StubTokenizer


class TestStubTokenizer:
    def test_encode_decode_roundtrip(self) -> None:
        tok = StubTokenizer()
        text = "hello world"
        ids = tok.encode(text)
        assert isinstance(ids, list)
        assert len(ids) == len(text)

    def test_encode_returns_ints(self) -> None:
        tok = StubTokenizer()
        ids = tok.encode("abc")
        assert all(isinstance(i, int) for i in ids)

    def test_decode_length(self) -> None:
        tok = StubTokenizer()
        ids = [65, 66, 67]
        result = tok.decode(ids)
        assert len(result) == 3


class TestStubModel:
    def test_generate_length(self) -> None:
        model = StubModel()
        prompt = [1, 2, 3]
        out = model.generate(prompt, max_new_tokens=16)
        assert len(out) == 16

    def test_generate_deterministic(self) -> None:
        model = StubModel()
        prompt = [10, 20, 30]
        out1 = model.generate(prompt, 8)
        out2 = model.generate(prompt, 8)
        assert out1 == out2

    def test_generate_differs_by_prompt(self) -> None:
        model = StubModel()
        out1 = model.generate([1], 8)
        out2 = model.generate([2], 8)
        assert out1 != out2

    def test_generate_zero_tokens(self) -> None:
        model = StubModel()
        out = model.generate([1, 2], 0)
        assert out == []

    def test_eval_noop(self) -> None:
        model = StubModel()
        model.eval()  # should not raise
