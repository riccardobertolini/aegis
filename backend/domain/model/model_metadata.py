"""Value object: local model metadata and version tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class QuantizationLevel(StrEnum):
    """Supported quantization levels."""
    NONE = "none"       # full precision (fp32 / fp16)
    INT8 = "int8"       # 8-bit integer
    INT4 = "int4"       # 4-bit integer (GPTQ / AWQ style)
    FP16 = "fp16"       # half precision
    BF16 = "bf16"       # bfloat16


class DeviceTarget(StrEnum):
    """Supported inference devices."""
    CPU  = "cpu"
    CUDA = "cuda"   # NVIDIA GPU
    MPS  = "mps"    # Apple Silicon
    AUTO = "auto"   # pick best available


@dataclass(frozen=True)
class ModelVersion:
    """Immutable version descriptor for a locally stored model."""
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, s: str) -> ModelVersion:
        parts = s.split(".")
        if len(parts) != 3:  # noqa: PLR2004
            raise ValueError(f"Invalid version string: {s!r}")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))


@dataclass
class ModelMetadata:
    """
    Describes a Mamba/SSM model stored on local disk.

    Stored alongside the checkpoint as ``<model_dir>/metadata.json``.
    """
    model_id: str                          # unique slug, e.g. "mamba-130m-v1"
    architecture: str = "mamba"            # "mamba" | "mamba2" | "ssm-custom"
    version: ModelVersion = field(default_factory=lambda: ModelVersion(1, 0, 0))
    description: str = ""
    language: str = "en"
    context_length: int = 2048
    hidden_dim: int = 768
    num_layers: int = 24
    vocab_size: int = 50257
    quantization: QuantizationLevel = QuantizationLevel.NONE
    # --- file references (relative to model directory) ---
    checkpoint_file: str = "model.pt"      # PyTorch state dict
    config_file: str = "config.json"       # Mamba config
    tokenizer_file: str = "tokenizer.json"
    # --- integrity ---
    sha256_checkpoint: str = ""            # filled by ModelSigner on registration
    sha256_tokenizer: str = ""
    signature: str = ""                    # HMAC-SHA256 over metadata fields
    # --- provenance ---
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: list[str] = field(default_factory=list)

    def checkpoint_path(self, models_dir: Path) -> Path:
        return models_dir / self.model_id / self.checkpoint_file

    def config_path(self, models_dir: Path) -> Path:
        return models_dir / self.model_id / self.config_file

    def tokenizer_path(self, models_dir: Path) -> Path:
        return models_dir / self.model_id / self.tokenizer_file

    def metadata_path(self, models_dir: Path) -> Path:
        return models_dir / self.model_id / "metadata.json"
