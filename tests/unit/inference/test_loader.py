"""Unit tests for MambaModelLoader."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.infrastructure.inference.loader import MambaModelLoader

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def models_root(tmp_path: Path) -> Path:
    return tmp_path / "models"


def _create_model_dir(root: Path, name: str, cfg: dict | None = None) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    config = cfg or {
        "model_type": "mamba",
        "d_model": 256,
        "n_layer": 8,
        "vocab_size": 512,
    }
    (d / "config.json").write_text(json.dumps(config))
    return d


# ---------------------------------------------------------------------------
# scan()
# ---------------------------------------------------------------------------

def test_scan_empty_dir(models_root: Path):
    models_root.mkdir()
    loader = MambaModelLoader(models_root)
    assert loader.scan() == []


def test_scan_missing_dir(tmp_path: Path):
    loader = MambaModelLoader(tmp_path / "nonexistent")
    assert loader.scan() == []


def test_scan_finds_valid_model(models_root: Path):
    _create_model_dir(models_root, "my-mamba")
    loader = MambaModelLoader(models_root)
    found = loader.scan()
    assert "my-mamba" in found


def test_scan_skips_dir_without_config(models_root: Path):
    (models_root / "bad-model").mkdir(parents=True)
    loader = MambaModelLoader(models_root)
    assert loader.scan() == []


def test_scan_multiple_models(models_root: Path):
    for name in ("model-a", "model-b", "model-c"):
        _create_model_dir(models_root, name)
    loader = MambaModelLoader(models_root)
    found = loader.scan()
    assert set(found) == {"model-a", "model-b", "model-c"}


# ---------------------------------------------------------------------------
# get_meta()
# ---------------------------------------------------------------------------

def test_get_meta_returns_correct_fields(models_root: Path):
    _create_model_dir(
        models_root, "test-model",
        cfg={"model_type": "mamba2", "d_model": 512, "n_layer": 16, "vocab_size": 1024},
    )
    loader = MambaModelLoader(models_root)
    loader.scan()
    meta = loader.get_meta("test-model")
    assert meta is not None
    assert meta.architecture == "mamba2"
    assert meta.d_model == 512
    assert meta.n_layer == 16
    assert meta.vocab_size == 1024


def test_get_meta_missing_returns_none(models_root: Path):
    models_root.mkdir()
    loader = MambaModelLoader(models_root)
    assert loader.get_meta("ghost") is None


# ---------------------------------------------------------------------------
# load() — weight file required
# ---------------------------------------------------------------------------

def test_load_raises_if_no_weight_file(models_root: Path):
    _create_model_dir(models_root, "no-weights")
    loader = MambaModelLoader(models_root)
    loader.scan()
    with pytest.raises((FileNotFoundError, ImportError)):
        loader.load("no-weights")


def test_load_unknown_model_raises(models_root: Path):
    models_root.mkdir()
    loader = MambaModelLoader(models_root)
    with pytest.raises(FileNotFoundError):
        loader.load("unknown-model")


# ---------------------------------------------------------------------------
# is_loaded() / unload()
# ---------------------------------------------------------------------------

def test_is_loaded_false_initially(models_root: Path):
    _create_model_dir(models_root, "m")
    loader = MambaModelLoader(models_root)
    loader.scan()
    assert loader.is_loaded("m") is False


def test_unload_noop_for_unloaded_model(models_root: Path):
    models_root.mkdir()
    loader = MambaModelLoader(models_root)
    loader.unload("ghost")  # should not raise
