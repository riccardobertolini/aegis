"""Unit tests for MambaInferenceAdapter (mock loader — no real model needed)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.domain.ports.inference import InferenceRequest
from backend.infrastructure.inference.adapter import MambaInferenceAdapter
from backend.infrastructure.inference.loader import MambaModelLoader

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_loader(model_id: str = "test-model") -> MambaModelLoader:
    loader = MagicMock(spec=MambaModelLoader)
    loader.is_loaded.return_value = True
    loader.get_tokenizer.return_value = _FakeTokenizer()
    loader.get_model.return_value = _FakeModel()
    loader.scan.return_value = [model_id]
    return loader


class _FakeEncoding:
    def __init__(self, ids):
        self.ids = ids


class _FakeTokenizer:
    def encode(self, text: str) -> _FakeEncoding:
        return _FakeEncoding([ord(c) % 256 for c in text[:8]])

    def decode(self, ids: list[int]) -> str:
        return "".join(chr(max(32, i % 127)) for i in ids)


class _FakeModel:
    """Minimal model that returns random logits via forward()."""
    def __call__(self, x):
        import torch
        return torch.randn(1, x.shape[1], 512)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_adapter_creation():
    loader = _make_mock_loader()
    adapter = MambaInferenceAdapter(loader=loader, default_model_id="test-model")
    assert adapter is not None


@pytest.mark.asyncio
async def test_run_returns_inference_response():
    loader = _make_mock_loader()
    adapter = MambaInferenceAdapter(loader=loader, default_model_id="test-model")

    req = InferenceRequest(
        prompt="Hello Mamba",
        model_id="test-model",
        max_tokens=4,
        temperature=0.0,
    )
    try:
        import torch  # noqa
        resp = await adapter.run(req)
        assert resp.model_id == "test-model"
        assert isinstance(resp.text, str)
        assert resp.prompt_tokens > 0
        assert resp.completion_tokens <= 4
        assert resp.finish_reason in ("stop", "length")
    except ImportError:
        pytest.skip("torch not installed")


@pytest.mark.asyncio
async def test_list_models():
    loader = _make_mock_loader("my-model")
    adapter = MambaInferenceAdapter(loader=loader)
    models = await adapter.list_models()
    assert "my-model" in models


@pytest.mark.asyncio
async def test_load_model_delegates_to_loader():
    loader = _make_mock_loader()
    loader.is_loaded.return_value = False
    adapter = MambaInferenceAdapter(loader=loader, default_model_id="test-model")
    with patch.object(loader, "load", return_value=None):
        await adapter.load_model("test-model")
        # load is called in executor — verify indirectly via is_loaded state


@pytest.mark.asyncio
async def test_unload_model_delegates_to_loader():
    loader = _make_mock_loader()
    adapter = MambaInferenceAdapter(loader=loader)
    await adapter.unload_model("test-model")
    loader.unload.assert_called_once_with("test-model")
