"""Integration tests — StorageManager (local filesystem, no network)."""
from __future__ import annotations

import pytest

from backend.infrastructure.adapters.encryption import EncryptionService
from backend.infrastructure.adapters.storage import StorageManager


@pytest.fixture
def storage(tmp_path):
    enc = EncryptionService(key_dir=str(tmp_path / "keys"))
    return StorageManager(
        encryption=enc,
        base_dir=str(tmp_path / "storage"),
    )


def test_store_and_retrieve_document(storage, tmp_path):
    content = b"PDF content placeholder"
    src = tmp_path / "doc.pdf"
    src.write_bytes(content)
    dest_path = storage.store_document(str(src), "doc.pdf", encrypt=False)
    assert dest_path is not None
    retrieved = storage.retrieve(dest_path)
    assert retrieved == content


def test_store_encrypted_document(storage, tmp_path):
    content = b"Sensitive document payload"
    src = tmp_path / "secret.pdf"
    src.write_bytes(content)
    dest_path = storage.store_document(str(src), "secret.pdf", encrypt=True)
    # The stored file must NOT be readable as plaintext
    import pathlib
    raw = pathlib.Path(dest_path).read_bytes()
    assert raw != content
    retrieved = storage.retrieve(dest_path, encrypted=True)
    assert retrieved == content


def test_integrity_check(storage, tmp_path):
    content = b"Integrity check payload"
    src = tmp_path / "file.bin"
    src.write_bytes(content)
    dest_path = storage.store_document(str(src), "file.bin", encrypt=False)
    assert storage.verify_integrity(dest_path) is True
    # Corrupt the file
    import pathlib
    p = pathlib.Path(dest_path)
    p.write_bytes(b"tampered")
    assert storage.verify_integrity(dest_path) is False


def test_delete_document(storage, tmp_path):
    import pathlib
    content = b"to be deleted"
    src = tmp_path / "del.txt"
    src.write_bytes(content)
    dest_path = storage.store_document(str(src), "del.txt", encrypt=False)
    storage.delete(dest_path)
    assert not pathlib.Path(dest_path).exists()
