"""Unit tests: AES-256-GCM LocalKeyStore."""
import pytest
from pathlib import Path

from backend.infrastructure.security.encryption import LocalKeyStore


@pytest.fixture
def keystore(tmp_path):
    return LocalKeyStore(
        keystore_path=str(tmp_path / "test_keystore.bin"),
        passphrase="test-passphrase-never-use-in-prod",
    )


def test_encrypt_decrypt_roundtrip(keystore):
    plaintext = b"Hello, Aegis!"
    ciphertext = keystore.encrypt(plaintext)
    assert ciphertext != plaintext
    assert keystore.decrypt(ciphertext) == plaintext


def test_different_encryptions_produce_different_ciphertext(keystore):
    pt = b"same message"
    assert keystore.encrypt(pt) != keystore.encrypt(pt)  # different nonces


def test_keystore_persists_across_instances(tmp_path):
    path = str(tmp_path / "ks.bin")
    ks1 = LocalKeyStore(path, "passphrase")
    ciphertext = ks1.encrypt(b"persistent data")
    ks2 = LocalKeyStore(path, "passphrase")
    assert ks2.decrypt(ciphertext) == b"persistent data"


def test_key_rotation_still_decrypts_old_data(keystore):
    ct_before = keystore.encrypt(b"old data")
    keystore.rotate()
    # Old ciphertext still decryptable because key ID is embedded
    assert keystore.decrypt(ct_before) == b"old data"


def test_new_data_uses_new_key_after_rotation(keystore):
    old_kid = keystore.active_key_id()
    keystore.rotate()
    new_kid = keystore.active_key_id()
    assert old_kid != new_kid
