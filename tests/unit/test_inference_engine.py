"""Unit tests for InferenceEngine using the stub backend."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.application.inference.inference_engine import InferenceEngine
from backend.domain.model.model_metadata import ModelMetadata, ModelVersion
from backend.domain.model.runtime_config import RuntimeConfig
from backend.domain.ports.inference import InferenceRequest
from backend.domain.ports.model_provider import IModelProvider
from backend.infrastructure.adapters.inference._stub_backend import StubModel, StubTokenizer
from backend.infrastructure.adapters.inference.context_manager import ContextManager
from backend.infrastructure.adapters.inference.model_registry import ModelRegistry
from backend.infrastructure.adapters.inference.model_signer import ModelSigner
from backend.shared.exceptions import ModelNotFoundError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def stub_meta() -> ModelMetadata:
    return ModelMetadata(
        model_id="stub-model",
        architecture="mamba",
        version=ModelVersion(1, 0, 0),
        vocab_size=256,
        sha256_checkpoint="",  # empty → skip integrity check
    )


@pytest.fixture()
def registry(tmp_path: Path, stub_meta: ModelMetadata) -> ModelRegistry:
    signer = ModelSigner(secret_key=b"test-key-32-bytes-padding-here!!")
    reg = ModelRegistry(models_dir=tmp_path / "models", signer=signer)
    reg.register(stub_meta)
    return reg


class _FakeProvider(IModelProvider):
    """In-memory fake provider backed by StubModel."""

    def __init__(self) -> None:
        self._models: dict[str, tuple[StubModel, StubTokenizer]] = {}

    async def load(self, metadata: ModelMetadata, config: RuntimeConfig) -> None:
        self._models[metadata.model_id] = (
            StubModel(metadata.vocab_size),
            StubTokenizer(metadata.vocab_size),
        )

    async def unload(self, model_id: str) -> None:
        self._models.pop(model_id, None)

    def is_loaded(self, model_id: str) -> bool:
        return model_id in self._models

    async def generate(self, model_id: str, prompt_ids: list[int], config: RuntimeConfig) -> list[int]:
        model, _ = self._models[model_id]
        return model.generate(prompt_ids, config.max_new_tokens)

    async def stream_generate(
        self, model_id: str, prompt_ids: list[int], config: RuntimeConfig
    ) -> AsyncIterator[int]:
        model, _ = self._models[model_id]
        for tok in model.generate(prompt_ids, config.max_new_tokens):
            yield tok

    async def encode(self, model_id: str, text: str) -> list[int]:
        _, tok = self._models[model_id]
        return tok.encode(text)

    async def decode(self, model_id: str, token_ids: list[int]) -> str:
        _, tok = self._models[model_id]
        return tok.decode(token_ids)


@pytest.fixture()
def engine(registry: ModelRegistry) -> InferenceEngine:
    provider = _FakeProvider()
    ctx = ContextManager()
    cfg = RuntimeConfig(max_new_tokens=8)
    return InferenceEngine(provider=provider, registry=registry, context_manager=ctx, default_config=cfg)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInferenceEngine:
    def test_list_models(self, engine: InferenceEngine) -> None:
        models = asyncio.get_event_loop().run_until_complete(engine.list_models())
        assert "stub-model" in models

    def test_run_returns_response(self, engine: InferenceEngine) -> None:
        req = InferenceRequest(prompt="hello", model_id="stub-model", max_tokens=8)
        resp = asyncio.get_event_loop().run_until_complete(engine.run(req))
        assert resp.model_id == "stub-model"
        assert resp.completion_tokens == 8
        assert isinstance(resp.text, str)

    def test_run_unknown_model_raises(self, engine: InferenceEngine) -> None:
        req = InferenceRequest(prompt="hello", model_id="nonexistent", max_tokens=4)
        with pytest.raises(ModelNotFoundError):
            asyncio.get_event_loop().run_until_complete(engine.run(req))

    def test_stream_yields_strings(self, engine: InferenceEngine) -> None:
        req = InferenceRequest(prompt="hello", model_id="stub-model", max_tokens=4, stream=True)

        async def _collect():
            tokens = []
            async for t in engine.stream(req):
                tokens.append(t)
            return tokens

        tokens = asyncio.get_event_loop().run_until_complete(_collect())
        assert len(tokens) == 4
        assert all(isinstance(t, str) for t in tokens)

    def test_run_batch(self, engine: InferenceEngine) -> None:
        reqs = [
            InferenceRequest(prompt="q1", model_id="stub-model", max_tokens=4),
            InferenceRequest(prompt="q2", model_id="stub-model", max_tokens=4),
        ]
        results = asyncio.get_event_loop().run_until_complete(engine.run_batch(reqs))
        assert len(results) == 2

    def test_load_and_unload(self, engine: InferenceEngine) -> None:
        asyncio.get_event_loop().run_until_complete(engine.load_model("stub-model"))
        asyncio.get_event_loop().run_until_complete(engine.unload_model("stub-model"))
        # After unload, running again should reload transparently
        req = InferenceRequest(prompt="test", model_id="stub-model", max_tokens=4)
        resp = asyncio.get_event_loop().run_until_complete(engine.run(req))
        assert resp.completion_tokens == 4
