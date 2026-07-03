"""Runtime configuration for a single inference session."""
from __future__ import annotations

from dataclasses import dataclass

from backend.domain.model.model_metadata import DeviceTarget, QuantizationLevel


@dataclass
class RuntimeConfig:
    """
    Tunable parameters for an inference run.

    These can be overridden per-request or set globally via Settings.
    """
    # Hardware
    device: DeviceTarget = DeviceTarget.AUTO
    quantization: QuantizationLevel = QuantizationLevel.NONE
    # Context
    max_context_length: int = 2048        # maximum tokens in rolling window
    max_new_tokens: int = 512
    # Sampling
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    # Performance
    batch_size: int = 1
    use_kv_cache: bool = True
    # Context compression (Mamba-specific)
    enable_context_compression: bool = True
    compression_ratio: float = 0.5        # keep top 50 % of context tokens by importance
    incremental_summary_every_n: int = 256  # tokens between incremental summaries
    # Streaming
    stream_chunk_size: int = 1            # tokens per streamed chunk

    @classmethod
    def from_settings(cls, settings: object) -> RuntimeConfig:  # type: ignore[override]
        """Build a RuntimeConfig from application Settings (populated per-phase)."""
        return cls()
