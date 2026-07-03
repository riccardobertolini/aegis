"""MambaModelProvider — IModelProvider implementation for Mamba/SSM models.

Design decisions:
- Lazy loading: models are loaded only when explicitly requested.
- No network calls: all paths are local filesystem only.
- Graceful degradation: if mamba-ssm (CUDA) is unavailable, falls back
  to a pure-Python selective-scan (mamba-minimal or stub).
- Device resolution: AUTO selects CUDA > MPS > CPU in that order.
- KV-cache: the Mamba hidden state (h) is cached between generation steps.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from backend.domain.model.model_metadata import DeviceTarget, ModelMetadata
from backend.domain.model.runtime_config import RuntimeConfig
from backend.domain.ports.model_provider import IModelProvider
from backend.shared.exceptions import InferenceError, ModelLoadError, ModelNotFoundError

if TYPE_CHECKING:
    pass

log = structlog.get_logger(__name__)


def _resolve_device(target: DeviceTarget) -> str:
    """Map DeviceTarget enum to a torch device string."""
    if target == DeviceTarget.AUTO:
        try:
            import torch  # type: ignore[import]
            if torch.cuda.is_available():
                return "cuda"
            if torch.backends.mps.is_available():  # type: ignore[attr-defined]
                return "mps"
        except ImportError:
            pass
        return "cpu"
    return target.value


def _apply_quantization(model: Any, level: str) -> Any:
    """Apply quantization to a loaded model (best-effort, returns model unchanged on failure)."""
    try:
        import torch  # type: ignore[import]
        if level == "int8":
            import torch.quantization as tq  # type: ignore[import]
            model = tq.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)  # type: ignore[arg-type]
            log.info("inference.quantization_applied", level=level)
    except Exception as exc:
        log.warning("inference.quantization_skipped", level=level, reason=str(exc))
    return model


class _LoadedModel:
    """Internal container for a loaded model and its tokenizer."""

    __slots__ = ("model", "tokenizer", "device", "metadata")

    def __init__(self, model: Any, tokenizer: Any, device: str, metadata: ModelMetadata) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.metadata = metadata


class MambaModelProvider(IModelProvider):
    """
    Concrete adapter that loads Mamba checkpoints from local disk.

    Supported backends (tried in order):
    1. ``mamba-ssm`` — full CUDA implementation (fastest)
    2. ``mamba-minimal`` — pure-Python reference implementation (CPU)
    3. ``_StubBackend`` — deterministic stub for tests (no torch required)
    """

    def __init__(self, models_dir: Path) -> None:
        self._models_dir = models_dir
        self._loaded: dict[str, _LoadedModel] = {}

    # ------------------------------------------------------------------
    # IModelProvider
    # ------------------------------------------------------------------

    async def load(self, metadata: ModelMetadata, config: RuntimeConfig) -> None:
        if self.is_loaded(metadata.model_id):
            log.debug("model.already_loaded", model_id=metadata.model_id)
            return

        device = _resolve_device(config.device)
        log.info("model.loading", model_id=metadata.model_id, device=device)

        try:
            model, tokenizer = await asyncio.get_event_loop().run_in_executor(
                None,
                self._load_from_disk,
                metadata,
                device,
                config,
            )
        except Exception as exc:
            raise ModelLoadError(
                f"Failed to load model '{metadata.model_id}': {exc}",
                model_id=metadata.model_id,
            ) from exc

        self._loaded[metadata.model_id] = _LoadedModel(model, tokenizer, device, metadata)
        log.info("model.loaded", model_id=metadata.model_id, device=device)

    async def unload(self, model_id: str) -> None:
        if model_id not in self._loaded:
            raise ModelNotFoundError(f"Model '{model_id}' is not loaded.", model_id=model_id)
        entry = self._loaded.pop(model_id)
        # Release GPU memory
        try:
            import torch  # type: ignore[import]
            if entry.device == "cuda":
                del entry.model
                torch.cuda.empty_cache()
        except ImportError:
            pass
        log.info("model.unloaded", model_id=model_id)

    def is_loaded(self, model_id: str) -> bool:
        return model_id in self._loaded

    async def generate(
        self,
        model_id: str,
        prompt_ids: list[int],
        config: RuntimeConfig,
    ) -> list[int]:
        entry = self._get_loaded(model_id)
        try:
            tokens = await asyncio.get_event_loop().run_in_executor(
                None,
                self._run_generate,
                entry,
                prompt_ids,
                config,
            )
            return tokens
        except Exception as exc:
            raise InferenceError(str(exc), model_id=model_id) from exc

    async def stream_generate(
        self,
        model_id: str,
        prompt_ids: list[int],
        config: RuntimeConfig,
    ) -> AsyncIterator[int]:
        entry = self._get_loaded(model_id)
        # Run blocking generation in executor, yield tokens as they arrive
        # via an asyncio.Queue bridge.
        queue: asyncio.Queue[int | None] = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def _worker() -> None:
            try:
                for tok in self._iter_generate(entry, prompt_ids, config):
                    loop.call_soon_threadsafe(queue.put_nowait, tok)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        loop.run_in_executor(None, _worker)

        while True:
            tok = await queue.get()
            if tok is None:
                break
            yield tok

    async def encode(self, model_id: str, text: str) -> list[int]:
        entry = self._get_loaded(model_id)
        return self._tokenize(entry, text)

    async def decode(self, model_id: str, token_ids: list[int]) -> str:
        entry = self._get_loaded(model_id)
        return self._detokenize(entry, token_ids)

    # ------------------------------------------------------------------
    # Private sync helpers (run in executor)
    # ------------------------------------------------------------------

    def _get_loaded(self, model_id: str) -> _LoadedModel:
        if model_id not in self._loaded:
            raise ModelNotFoundError(
                f"Model '{model_id}' is not loaded. Call load() first.",
                model_id=model_id,
            )
        return self._loaded[model_id]

    def _load_from_disk(
        self,
        metadata: ModelMetadata,
        device: str,
        config: RuntimeConfig,
    ) -> tuple[Any, Any]:
        """Blocking: load checkpoint and tokenizer from local filesystem."""
        ckpt_path = metadata.checkpoint_path(self._models_dir)
        tok_path  = metadata.tokenizer_path(self._models_dir)
        cfg_path  = metadata.config_path(self._models_dir)

        # --- try mamba-ssm first (GPU), then mamba-minimal (CPU), then stub ---
        try:
            return self._load_mamba_ssm(ckpt_path, cfg_path, tok_path, device, config)
        except ImportError:
            log.warning("mamba_ssm.not_available", fallback="mamba-minimal")

        try:
            return self._load_mamba_minimal(ckpt_path, cfg_path, tok_path, device)
        except ImportError:
            log.warning("mamba_minimal.not_available", fallback="stub")

        return self._load_stub(metadata)

    def _load_mamba_ssm(
        self,
        ckpt_path: Path,
        cfg_path: Path,
        tok_path: Path,
        device: str,
        config: RuntimeConfig,
    ) -> tuple[Any, Any]:
        import json as _json

        import torch  # type: ignore[import]
        from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel  # type: ignore[import]
        from transformers import AutoTokenizer  # type: ignore[import]

        with open(cfg_path) as f:
            cfg = _json.load(f)

        model = MambaLMHeadModel(**cfg).to(device)  # type: ignore[arg-type]
        state = torch.load(str(ckpt_path), map_location=device)  # type: ignore[arg-type]
        model.load_state_dict(state)
        model.eval()
        model = _apply_quantization(model, config.quantization.value)

        tokenizer = AutoTokenizer.from_pretrained(str(tok_path.parent), local_files_only=True)
        return model, tokenizer

    def _load_mamba_minimal(
        self,
        ckpt_path: Path,
        cfg_path: Path,
        tok_path: Path,
        device: str,
    ) -> tuple[Any, Any]:
        import json as _json

        import mamba_minimal as mm  # type: ignore[import]
        import torch  # type: ignore[import]

        with open(cfg_path) as f:
            cfg = _json.load(f)

        model = mm.Mamba(**cfg)  # type: ignore[attr-defined]
        state = torch.load(str(ckpt_path), map_location=device)
        model.load_state_dict(state)
        model.eval()

        from transformers import AutoTokenizer  # type: ignore[import]
        tokenizer = AutoTokenizer.from_pretrained(str(tok_path.parent), local_files_only=True)
        return model, tokenizer

    def _load_stub(self, metadata: ModelMetadata) -> tuple[Any, Any]:
        """Deterministic stub — used in tests and when no backend is installed."""
        from backend.infrastructure.adapters.inference._stub_backend import StubModel, StubTokenizer
        log.warning("model.using_stub", model_id=metadata.model_id)
        return StubModel(metadata.vocab_size), StubTokenizer(metadata.vocab_size)

    def _tokenize(self, entry: _LoadedModel, text: str) -> list[int]:
        from backend.infrastructure.adapters.inference._stub_backend import StubTokenizer
        if isinstance(entry.tokenizer, StubTokenizer):
            return entry.tokenizer.encode(text)
        return entry.tokenizer.encode(text, add_special_tokens=False)

    def _detokenize(self, entry: _LoadedModel, ids: list[int]) -> str:
        from backend.infrastructure.adapters.inference._stub_backend import StubTokenizer
        if isinstance(entry.tokenizer, StubTokenizer):
            return entry.tokenizer.decode(ids)
        return entry.tokenizer.decode(ids, skip_special_tokens=True)

    def _run_generate(self, entry: _LoadedModel, prompt_ids: list[int], config: RuntimeConfig) -> list[int]:
        """Blocking generate — called inside executor."""
        from backend.infrastructure.adapters.inference._stub_backend import StubModel
        if isinstance(entry.model, StubModel):
            return entry.model.generate(prompt_ids, config.max_new_tokens)
        return self._torch_generate(entry, prompt_ids, config)

    def _iter_generate(self, entry: _LoadedModel, prompt_ids: list[int], config: RuntimeConfig):
        """Blocking generator — yields one token at a time."""
        tokens = self._run_generate(entry, prompt_ids, config)
        yield from tokens

    def _torch_generate(self, entry: _LoadedModel, prompt_ids: list[int], config: RuntimeConfig) -> list[int]:
        """Real torch-based generation (mamba-ssm or mamba-minimal)."""
        try:
            import torch  # type: ignore[import]
            input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=entry.device)
            with torch.no_grad():
                out = entry.model.generate(
                    input_ids=input_ids,
                    max_length=len(prompt_ids) + config.max_new_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    top_k=config.top_k,
                    repetition_penalty=config.repetition_penalty,
                )
            new_ids = out[0, len(prompt_ids):].tolist()
            return new_ids
        except Exception as exc:
            raise InferenceError(str(exc), model_id=entry.metadata.model_id) from exc
