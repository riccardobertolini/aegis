"""Unit tests for CoreAIService."""
import asyncio
from pathlib import Path

import pytest

from backend.application.inference.core_ai_service import CoreAIService
from backend.application.inference.inference_engine import InferenceEngine
from backend.domain.model.model_metadata import ModelMetadata, ModelVersion
from backend.domain.model.runtime_config import RuntimeConfig
from backend.domain.ports.core_ai import AIRequest
from backend.infrastructure.adapters.inference.context_manager import ContextManager
from backend.infrastructure.adapters.inference.model_registry import ModelRegistry
from backend.infrastructure.adapters.inference.model_signer import ModelSigner
from tests.unit.test_inference_engine import _FakeProvider


@pytest.fixture
def core_ai_service(tmp_path: Path) -> CoreAIService:
    meta = ModelMetadata(
        model_id="stub-model",
        version=ModelVersion(1, 0, 0),
        vocab_size=256,
        sha256_checkpoint="",
    )
    signer = ModelSigner(secret_key=b"test-key-32-bytes-padding-here!!")
    registry = ModelRegistry(models_dir=tmp_path / "models", signer=signer)
    registry.register(meta)

    provider = _FakeProvider()
    ctx = ContextManager()
    cfg = RuntimeConfig(max_new_tokens=8)
    engine = InferenceEngine(provider=provider, registry=registry, context_manager=ctx, default_config=cfg)
    return CoreAIService(inference_engine=engine, default_model_id="stub-model")


class TestCoreAIService:
    def test_process_returns_ai_response(self, core_ai_service: CoreAIService) -> None:
        req = AIRequest(session_id="s1", user_input="hello world")
        resp = asyncio.get_event_loop().run_until_complete(core_ai_service.process(req))
        assert resp.session_id == "s1"
        assert isinstance(resp.text, str)
        assert "inference" in resp.engine_trace

    def test_engine_trace_populated(self, core_ai_service: CoreAIService) -> None:
        req = AIRequest(session_id="s2", user_input="test")
        resp = asyncio.get_event_loop().run_until_complete(core_ai_service.process(req))
        assert len(resp.engine_trace) >= 1
