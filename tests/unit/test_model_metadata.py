"""Unit tests for ModelMetadata and ModelVersion value objects."""
from pathlib import Path

import pytest

from backend.domain.model.model_metadata import (
    ModelMetadata,
    ModelVersion,
    QuantizationLevel,
)


class TestModelVersion:
    def test_from_string_valid(self) -> None:
        v = ModelVersion.from_string("2.1.3")
        assert v == ModelVersion(2, 1, 3)

    def test_str_roundtrip(self) -> None:
        v = ModelVersion(1, 2, 3)
        assert str(v) == "1.2.3"

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError):
            ModelVersion.from_string("1.0")

    def test_immutable(self) -> None:
        v = ModelVersion(1, 0, 0)
        with pytest.raises(Exception):
            v.major = 2  # type: ignore[misc]


class TestModelMetadata:
    def test_checkpoint_path(self) -> None:
        meta = ModelMetadata(model_id="mamba-130m")
        base = Path("/models")
        assert meta.checkpoint_path(base) == Path("/models/mamba-130m/model.pt")

    def test_metadata_path(self) -> None:
        meta = ModelMetadata(model_id="mamba-130m")
        base = Path("/models")
        assert meta.metadata_path(base) == Path("/models/mamba-130m/metadata.json")

    def test_defaults(self) -> None:
        meta = ModelMetadata(model_id="test-model")
        assert meta.architecture == "mamba"
        assert meta.quantization == QuantizationLevel.NONE
        assert meta.sha256_checkpoint == ""
