"""Integration tests — EncryptionService (local, no network)."""
from __future__ import annotations

import os
import tempfile

import pytest

from backend.infrastructure.adapters.encryption import EncryptionService


@pytest.fixture
def enc_service(tmp_path):
    """EncryptionService using a temporary key directory."""
    return EncryptionService(key_dir=str(tmp_path))


def test_encrypt_decrypt_roundtrip(enc_service):
    plaintext = b"Aegis secret payload 42"
    ciphertext = enc_service.encrypt(plaintext)
    assert ciphertext != plaintext
    recovered = enc_service.decrypt(ciphertext)
    assert recovered == plaintext


def test_encrypt_string_roundtrip(enc_service):
    original = "Configurazione assistente privato"
    encrypted = enc_service.encrypt_str(original)
    assert encrypted != original
    assert enc_service.decrypt_str(encrypted) == original


def test_different_ciphertexts_same_plaintext(enc_service):
    """AES-GCM with random nonce must produce different ciphertexts."""
    pt = b"same plaintext"
    c1 = enc_service.encrypt(pt)
    c2 = enc_service.encrypt(pt)
    assert c1 != c2


def test_key_persistence(tmp_path):
    """Two EncryptionService instances sharing the same key dir must interoperate."""
    enc1 = EncryptionService(key_dir=str(tmp_path))
    enc2 = EncryptionService(key_dir=str(tmp_path))
    msg = b"cross-instance roundtrip"
    assert enc2.decrypt(enc1.encrypt(msg)) == msg


def test_file_encrypt_decrypt(enc_service, tmp_path):
    src = tmp_path / "plain.txt"
    dst = tmp_path / "plain.enc"
    out = tmp_path / "plain.dec"
    src.write_bytes(b"File content to protect")
    enc_service.encrypt_file(str(src), str(dst))
    assert dst.exists()
    enc_service.decrypt_file(str(dst), str(out))
    assert out.read_bytes() == src.read_bytes()
