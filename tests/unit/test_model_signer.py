"""Unit tests for ModelSigner — file hashing and HMAC signing."""
import json
import tempfile
from pathlib import Path

import pytest

from backend.infrastructure.adapters.inference.model_signer import ModelSigner


@pytest.fixture()
def signer() -> ModelSigner:
    return ModelSigner(secret_key=b"test-secret-key-32-bytes-padding!")


class TestHashFile:
    def test_known_content(self, signer: ModelSigner, tmp_path: Path) -> None:
        import hashlib
        f = tmp_path / "file.bin"
        content = b"aegis model weights"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert signer.hash_file(f) == expected

    def test_large_file_streaming(self, signer: ModelSigner, tmp_path: Path) -> None:
        import hashlib
        f = tmp_path / "large.bin"
        content = b"x" * (9 * 1024 * 1024)  # 9 MB — crosses chunk boundary
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert signer.hash_file(f) == expected


class TestVerifyFile:
    def test_valid_hash(self, signer: ModelSigner, tmp_path: Path) -> None:
        f = tmp_path / "model.pt"
        f.write_bytes(b"weights")
        h = signer.hash_file(f)
        assert signer.verify_file(f, h) is True

    def test_tampered_file(self, signer: ModelSigner, tmp_path: Path) -> None:
        f = tmp_path / "model.pt"
        f.write_bytes(b"original")
        h = signer.hash_file(f)
        f.write_bytes(b"tampered")
        assert signer.verify_file(f, h) is False

    def test_empty_hash_returns_false(self, signer: ModelSigner, tmp_path: Path) -> None:
        f = tmp_path / "model.pt"
        f.write_bytes(b"data")
        assert signer.verify_file(f, "") is False

    def test_missing_file_returns_false(self, signer: ModelSigner, tmp_path: Path) -> None:
        f = tmp_path / "nonexistent.pt"
        assert signer.verify_file(f, "abc123") is False


class TestSignMetadata:
    def test_signature_is_deterministic(self, signer: ModelSigner) -> None:
        meta = {"model_id": "mamba-130m", "version": "1.0.0", "architecture": "mamba"}
        sig1 = signer.sign_metadata(meta)
        sig2 = signer.sign_metadata(meta)
        assert sig1 == sig2

    def test_signature_changes_with_content(self, signer: ModelSigner) -> None:
        meta1 = {"model_id": "mamba-130m"}
        meta2 = {"model_id": "mamba-370m"}
        assert signer.sign_metadata(meta1) != signer.sign_metadata(meta2)

    def test_verify_valid_signature(self, signer: ModelSigner) -> None:
        meta = {"model_id": "mamba-130m", "architecture": "mamba"}
        meta["signature"] = signer.sign_metadata(meta)
        assert signer.verify_metadata(meta) is True

    def test_verify_rejects_tampered_signature(self, signer: ModelSigner) -> None:
        meta = {"model_id": "mamba-130m", "signature": "deadbeef"}
        assert signer.verify_metadata(meta) is False

    def test_signature_field_excluded_from_payload(self, signer: ModelSigner) -> None:
        meta = {"model_id": "x", "architecture": "mamba"}
        sig_without = signer.sign_metadata(meta)
        meta["signature"] = "some-old-sig"
        sig_with = signer.sign_metadata(meta)
        assert sig_without == sig_with
