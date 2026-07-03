"""InferenceEngine — application-layer service orchestrating the inference pipeline.

Responsibilities:
- Load models on demand (using ModelRegistry + ModelSigner for integrity).
- Build prompt token sequences from the ContextManager.
- Delegate actual generation to IModelProvider.
- Handle streaming, batching, context compression.
- No network calls anywhere in this file.
"""
from __future__ import annotations

import time
from collections.abc import AsyncIterator

import structlog

from backend.domain.model.model_metadata import ModelMetadata
from backend.domain.model.runtime_config import RuntimeConfig
from backend.domain.ports.inference import InferenceRequest, InferenceResponse
from backend.domain.ports.model_provider import IModelProvider
from backend.infrastructure.adapters.inference.context_manager import ContextManager
from backend.infrastructure.adapters.inference.model_registry import ModelRegistry
from backend.shared.exceptions import InferenceError, ModelLoadError

log = structlog.get_logger(__name__)


class InferenceEngine:
    """
    Orchestrates: Registry → Integrity → Load → Context → Generate.

    This is the main entry point used by FastAPI routers and CoreAIService.
    """

    def __init__(
        self,
        provider: IModelProvider,
        registry: ModelRegistry,
        context_manager: ContextManager,
        default_config: RuntimeConfig | None = None,
    ) -> None:
        self._provider = provider
        self._registry = registry
        self._ctx = context_manager
        self._default_config = default_config or RuntimeConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, request: InferenceRequest) -> InferenceResponse:
        """Execute a full inference pass and return the complete response."""
        t0 = time.monotonic()
        config = self._merge_config(request)
        meta = await self._ensure_loaded(request.model_id)

        # Build prompt
        prompt_ids = await self._build_prompt(request, meta)
        log.info("inference.run", model_id=request.model_id, prompt_tokens=len(prompt_ids))

        try:
            token_ids = await self._provider.generate(
                model_id=request.model_id,
                prompt_ids=prompt_ids,
                config=config,
            )
        except Exception as exc:
            raise InferenceError(str(exc), model_id=request.model_id) from exc

        text = await self._provider.decode(request.model_id, token_ids)

        # Update context
        if request.extra.get("session_id"):
            self._ctx.append(request.extra["session_id"], prompt_ids + token_ids, config)

        elapsed = time.monotonic() - t0
        log.info(
            "inference.complete",
            model_id=request.model_id,
            completion_tokens=len(token_ids),
            elapsed_s=round(elapsed, 3),
        )
        return InferenceResponse(
            text=text,
            model_id=request.model_id,
            prompt_tokens=len(prompt_ids),
            completion_tokens=len(token_ids),
            finish_reason="stop",
        )

    async def stream(self, request: InferenceRequest) -> AsyncIterator[str]:
        """Stream decoded tokens one by one."""
        config = self._merge_config(request)
        await self._ensure_loaded(request.model_id)
        prompt_ids = await self._build_prompt(request, self._registry.get(request.model_id))

        log.info("inference.stream", model_id=request.model_id, prompt_tokens=len(prompt_ids))
        async for token_id in self._provider.stream_generate(
            model_id=request.model_id,
            prompt_ids=prompt_ids,
            config=config,
        ):
            yield await self._provider.decode(request.model_id, [token_id])

    async def run_batch(self, requests: list[InferenceRequest]) -> list[InferenceResponse]:
        """Run multiple requests sequentially (true batching per-model in later phase)."""
        results: list[InferenceResponse] = []
        for req in requests:
            results.append(await self.run(req))
        return results

    async def list_models(self) -> list[str]:
        return [m.model_id for m in self._registry.list_all()]

    async def load_model(self, model_id: str) -> None:
        await self._ensure_loaded(model_id)

    async def unload_model(self, model_id: str) -> None:
        await self._provider.unload(model_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _ensure_loaded(self, model_id: str) -> ModelMetadata:
        meta = self._registry.get(model_id)  # raises ModelNotFoundError if missing
        if not self._provider.is_loaded(model_id):
            # Integrity check before loading
            if meta.sha256_checkpoint:
                ok = self._registry.verify_integrity(model_id)
                if not ok:
                    raise ModelLoadError(
                        f"Integrity check failed for model '{model_id}'. "
                        "The checkpoint may be corrupted or tampered.",
                        model_id=model_id,
                    )
            await self._provider.load(meta, self._default_config)
        return meta

    def _merge_config(self, request: InferenceRequest) -> RuntimeConfig:
        """Overlay per-request params on top of default RuntimeConfig."""
        cfg = RuntimeConfig(
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            device=self._default_config.device,
            quantization=self._default_config.quantization,
            max_context_length=self._default_config.max_context_length,
            use_kv_cache=self._default_config.use_kv_cache,
            enable_context_compression=self._default_config.enable_context_compression,
            compression_ratio=self._default_config.compression_ratio,
            stream_chunk_size=self._default_config.stream_chunk_size,
        )
        return cfg

    async def _build_prompt(self, request: InferenceRequest, meta: ModelMetadata) -> list[int]:
        """Tokenise the prompt; prepend session context if available."""
        session_id = request.extra.get("session_id")
        prompt_text = request.prompt

        if session_id:
            context_ids = self._ctx.build_prompt_ids(session_id)
            new_ids = await self._provider.encode(request.model_id, prompt_text)
            combined = context_ids + new_ids
            # Truncate to max_context_length
            max_len = self._default_config.max_context_length - request.max_tokens
            if len(combined) > max_len:
                combined = combined[-max_len:]
            return combined

        return await self._provider.encode(request.model_id, prompt_text)
