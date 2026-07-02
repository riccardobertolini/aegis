"""Unit tests for InferenceContainer wiring."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.infrastructure.inference.container import InferenceContainer
from backend.domain.ports.inference import IInferencePort
from backend.domain.ports.core_ai import ICoreAIPort


@pytest.fixture()
def empty_models_root(tmp_path: Path) -> Path:
    root = tmp_path / "models"
    root.mkdir()
    return root


def test_build_returns_container(empty_models_root: Path):
    container = InferenceContainer.build(models_root=empty_models_root)
    assert isinstance(container.inference, IInferencePort)
    assert isinstance(container.core_ai, ICoreAIPort)


def test_build_auto_selects_first_model(tmp_path: Path):
    root = tmp_path / "models"
    model_dir = root / "my-ssm"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text(
        json.dumps({"model_type": "mamba", "d_model": 128, "n_layer": 4, "vocab_size": 256})
    )
    container = InferenceContainer.build(models_root=root)
    # Adapter should have auto-selected the only available model as default
    assert container.loader.list_available() == ["my-ssm"]


def test_build_with_custom_system_prompt(empty_models_root: Path):
    container = InferenceContainer.build(
        models_root=empty_models_root,
        system_prompt="Custom prompt",
    )
    assert container.core_ai._system_prompt == "Custom prompt"
