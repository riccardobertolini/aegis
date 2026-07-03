"""Unit tests for ModelSigner."""
import json
from pathlib import Path

import pytest

from backend.infrastructure.training.signer import ModelSigner


@pytest.fixture
def model_dir(tmp_path) -> Path:
    d = tmp_path / "my-model"
    d.mkdir()
    (d / "config.json").write_text(json.dumps({"model_type": "mamba"}))
    (d / "model.pt").write_bytes(b"fake-weights" * 100)
    return d


def test_sign_creates_manifest(model_dir):
    signer = ModelSigner()
    manifest = signer.sign(model_dir)
    assert "files" in manifest
    assert (model_dir / "integrity.json").exists()


def test_verify_passes(model_dir):
    signer = ModelSigner()
    signer.sign(model_dir)
    assert signer.verify(model_dir) is True


def test_verify_fails_after_tamper(model_dir):
    signer = ModelSigner()
    signer.sign(model_dir)
    (model_dir / "model.pt").write_bytes(b"tampered-data")
    assert signer.verify(model_dir) is False


def test_sign_with_hmac(model_dir):
    signer = ModelSigner(hmac_secret=b"secret")
    manifest = signer.sign(model_dir)
    assert "hmac" in manifest


def test_hmac_verify_fails_wrong_secret(model_dir):
    signer = ModelSigner(hmac_secret=b"secret")
    signer.sign(model_dir)
    bad_signer = ModelSigner(hmac_secret=b"wrong")
    assert bad_signer.verify(model_dir) is False
