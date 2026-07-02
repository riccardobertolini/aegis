"""Latency and memory benchmark fixture.

NOT a correctness test — this file measures performance of the stub backend
so we have a baseline before real weights are integrated.

Run with: pytest tests/unit/test_benchmark_latency.py -v -s
"""
from __future__ import annotations

import asyncio
import time
import tracemalloc
from pathlib import Path

import pytest

from backend.application.inference.inference_engine import InferenceEngine
from backend.domain.model.model_metadata import ModelMetadata, ModelVersion
from backend.domain.model.runtime_config import RuntimeConfig
from backend.domain.ports.inference import InferenceRequest
from backend.infrastructure.adapters.inference.context_manager import ContextManager
from backend.infrastructure.adapters.inference.model_registry import ModelRegistry
from backend.infrastructure.adapters.inference.model_signer import ModelSigner
from tests.unit.test_inference_engine import _FakeProvider


@pytest.fixture(scope="module")
def bench_engine(tmp_path_factory) -> InferenceEngine:
    tmp = tmp_path_factory.mktemp("models")
    meta = ModelMetadata(
        model_id="stub-bench",
        version=ModelVersion(1, 0, 0),
        vocab_size=256,
        sha256_checkpoint="",
    )
    signer = ModelSigner(secret_key=b"bench-key-32-bytes-padding-here!")
    registry = ModelRegistry(models_dir=tmp / "models", signer=signer)
    registry.register(meta)
    provider = _FakeProvider()
    ctx = ContextManager()
    cfg = RuntimeConfig(max_new_tokens=64)
    return InferenceEngine(provider=provider, registry=registry, context_manager=ctx, default_config=cfg)


class TestBenchmark:
    """Benchmark stub latency and memory — must complete within generous thresholds."""

    LATENCY_THRESHOLD_S = 2.0   # stub must complete 64 tokens in < 2 s
    MEMORY_THRESHOLD_KB = 1024  # stub must not allocate > 1 MB peak

    def test_single_request_latency(self, bench_engine: InferenceEngine) -> None:
        req = InferenceRequest(prompt="benchmark", model_id="stub-bench", max_tokens=64)
        t0 = time.monotonic()
        asyncio.get_event_loop().run_until_complete(bench_engine.run(req))
        elapsed = time.monotonic() - t0
        print(f"\n[benchmark] single request latency: {elapsed*1000:.1f} ms")
        assert elapsed < self.LATENCY_THRESHOLD_S

    def test_batch_10_latency(self, bench_engine: InferenceEngine) -> None:
        reqs = [
            InferenceRequest(prompt=f"q{i}", model_id="stub-bench", max_tokens=16)
            for i in range(10)
        ]
        t0 = time.monotonic()
        asyncio.get_event_loop().run_until_complete(bench_engine.run_batch(reqs))
        elapsed = time.monotonic() - t0
        print(f"\n[benchmark] batch-10 latency: {elapsed*1000:.1f} ms")
        assert elapsed < self.LATENCY_THRESHOLD_S * 10

    def test_memory_single_request(self, bench_engine: InferenceEngine) -> None:
        req = InferenceRequest(prompt="memory test", model_id="stub-bench", max_tokens=64)
        tracemalloc.start()
        asyncio.get_event_loop().run_until_complete(bench_engine.run(req))
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_kb = peak / 1024
        print(f"\n[benchmark] peak memory: {peak_kb:.1f} KB")
        assert peak_kb < self.MEMORY_THRESHOLD_KB
