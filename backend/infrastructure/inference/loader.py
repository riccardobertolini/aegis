"""MambaModelLoader — scans models/ directory and loads SSM weights offline.

No network calls. Ever. Models must be copied manually into `models/`.
Supports both `mamba-ssm` (CUDA) and `mamba-minimal` (pure-Python CPU fallback).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelMeta:
    model_id: str
    path: Path
    architecture: str = "mamba"          # "mamba" | "mamba2" | "jamba"
    context_length: int = 2048
    d_model: int = 768
    n_layer: int = 24
    vocab_size: int = 50280
    extra: dict = field(default_factory=dict)

    @property
    def checksum(self) -> str:
        """SHA-256 of the primary weight file (.pt / .safetensors)."""
        weight_file = self._find_weight_file()
        if weight_file is None:
            return ""
        h = hashlib.sha256()
        with open(weight_file, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    def _find_weight_file(self) -> Optional[Path]:
        for ext in (".pt", ".pth", ".safetensors", ".bin"):
            for p in sorted(self.path.glob(f"*{ext}")):
                return p
        return None


_REQUIRED_FILES = ("config.json",)


class MambaModelLoader:
    """Discovers and loads Mamba/SSM models from a local directory tree.

    Expected layout::

        models/
            my-mamba-model/
                config.json        # must contain 'd_model', 'n_layer', 'vocab_size'
                model.safetensors  # or model.pt
                (tokenizer.json)   # optional
    """

    def __init__(self, models_root: str | Path) -> None:
        self._root = Path(models_root)
        self._meta_cache: dict[str, ModelMeta] = {}
        self._loaded: dict[str, Any] = {}  # model_id → loaded model object
        self._tokenizers: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def scan(self) -> list[str]:
        """Return model_ids of all valid model directories."""
        found: list[str] = []
        if not self._root.exists():
            logger.warning("models_root does not exist: %s", self._root)
            return found

        for entry in sorted(self._root.iterdir()):
            if not entry.is_dir():
                continue
            missing = [f for f in _REQUIRED_FILES if not (entry / f).exists()]
            if missing:
                logger.debug("Skipping %s — missing %s", entry.name, missing)
                continue
            meta = self._parse_config(entry)
            if meta:
                self._meta_cache[meta.model_id] = meta
                found.append(meta.model_id)
        logger.info("Discovered %d model(s): %s", len(found), found)
        return found

    def get_meta(self, model_id: str) -> Optional[ModelMeta]:
        return self._meta_cache.get(model_id)

    def list_available(self) -> list[str]:
        return list(self._meta_cache.keys())

    # ------------------------------------------------------------------
    # Load / Unload
    # ------------------------------------------------------------------

    def load(self, model_id: str) -> Any:
        """Load model into memory. Returns the model object."""
        if model_id in self._loaded:
            return self._loaded[model_id]

        meta = self._meta_cache.get(model_id)
        if meta is None:
            # Lazy scan in case models were dropped after startup
            self.scan()
            meta = self._meta_cache.get(model_id)
        if meta is None:
            raise FileNotFoundError(f"Model '{model_id}' not found in {self._root}")

        model = self._load_backend(meta)
        self._loaded[model_id] = model
        self._tokenizers[model_id] = self._load_tokenizer(meta)
        logger.info("Model '%s' loaded (arch=%s)", model_id, meta.architecture)
        return model

    def unload(self, model_id: str) -> None:
        if model_id in self._loaded:
            del self._loaded[model_id]
            self._tokenizers.pop(model_id, None)
            # Best-effort GPU memory release
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:
                pass
            logger.info("Model '%s' unloaded", model_id)

    def is_loaded(self, model_id: str) -> bool:
        return model_id in self._loaded

    def get_model(self, model_id: str) -> Any:
        return self._loaded.get(model_id)

    def get_tokenizer(self, model_id: str) -> Any:
        return self._tokenizers.get(model_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_config(self, directory: Path) -> Optional[ModelMeta]:
        config_path = directory / "config.json"
        try:
            with open(config_path) as f:
                cfg = json.load(f)
        except Exception as exc:
            logger.warning("Cannot parse %s: %s", config_path, exc)
            return None

        arch = cfg.get("model_type", "mamba")
        return ModelMeta(
            model_id=directory.name,
            path=directory,
            architecture=arch,
            context_length=cfg.get("max_position_embeddings", cfg.get("d_model", 2048)),
            d_model=cfg.get("d_model", 768),
            n_layer=cfg.get("n_layer", cfg.get("num_hidden_layers", 24)),
            vocab_size=cfg.get("vocab_size", 50280),
            extra=cfg,
        )

    def _load_backend(self, meta: ModelMeta) -> Any:
        """Try mamba-ssm (GPU) first, fall back to mamba-minimal (CPU)."""
        weight_file = meta._find_weight_file()
        if weight_file is None:
            raise FileNotFoundError(
                f"No weight file found in {meta.path}. "
                "Drop a .pt / .safetensors file there."
            )

        # --- GPU path: mamba-ssm ---
        try:
            return self._load_mamba_ssm(meta, weight_file)
        except ImportError:
            logger.info("mamba-ssm not available — falling back to mamba-minimal (CPU)")
        except Exception as exc:
            logger.warning("mamba-ssm load failed (%s) — trying CPU fallback", exc)

        # --- CPU path: mamba-minimal ---
        return self._load_mamba_minimal(meta, weight_file)

    def _load_mamba_ssm(self, meta: ModelMeta, weight_file: Path) -> Any:
        import torch  # noqa: F401 — guard import
        from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel  # type: ignore
        model = MambaLMHeadModel.from_pretrained(
            str(meta.path),
            device="cuda",
            dtype=None,  # use config dtype
        )
        model.eval()
        return model

    def _load_mamba_minimal(self, meta: ModelMeta, weight_file: Path) -> Any:
        """Load using the CPU-compatible mamba-minimal reference implementation."""
        try:
            import torch
            from mamba_minimal.model import Mamba, ModelArgs  # type: ignore

            args = ModelArgs(
                d_model=meta.d_model,
                n_layer=meta.n_layer,
                vocab_size=meta.vocab_size,
            )
            model = Mamba(args)
            state = torch.load(str(weight_file), map_location="cpu", weights_only=True)
            # Handle nested state dict formats
            if "model" in state:
                state = state["model"]
            elif "state_dict" in state:
                state = state["state_dict"]
            model.load_state_dict(state, strict=False)
            model.eval()
            return model
        except ImportError as exc:
            raise ImportError(
                "Neither mamba-ssm nor mamba-minimal is installed. "
                "See requirements/ml.txt for installation instructions."
            ) from exc

    def _load_tokenizer(self, meta: ModelMeta) -> Any:
        """Load tokenizer from model directory. Falls back to a no-op tokenizer."""
        tok_path = meta.path / "tokenizer.json"
        if tok_path.exists():
            try:
                from tokenizers import Tokenizer  # type: ignore
                return Tokenizer.from_file(str(tok_path))
            except ImportError:
                pass

        vocab_path = meta.path / "vocab.json"
        if vocab_path.exists():
            try:
                from tokenizers import Tokenizer  # type: ignore  # noqa
                return Tokenizer.from_file(str(vocab_path))
            except ImportError:
                pass

        logger.warning(
            "No tokenizer found for '%s' — using ByteLevelFallbackTokenizer",
            meta.model_id,
        )
        return _ByteLevelFallbackTokenizer()


# ---------------------------------------------------------------------------
# Fallback tokenizer (ASCII byte-level, last resort)
# ---------------------------------------------------------------------------

class _ByteLevelFallbackTokenizer:
    """Minimal byte-level tokenizer used only when no tokenizer.json is present."""

    def encode(self, text: str):
        ids = list(text.encode("utf-8"))
        return _FakeEncoding(ids)

    def decode(self, ids: list[int]) -> str:
        return bytes([i % 256 for i in ids]).decode("utf-8", errors="replace")


class _FakeEncoding:
    def __init__(self, ids: list[int]) -> None:
        self.ids = ids
