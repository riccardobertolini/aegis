"""Integration tests — BackupManager (local, no network)."""
from __future__ import annotations

import json
import pathlib

import pytest

from backend.infrastructure.adapters.backup_manager import BackupManager
from backend.infrastructure.adapters.encryption import EncryptionService
from backend.infrastructure.adapters.storage import StorageManager


@pytest.fixture
def backup_mgr(tmp_path):
    enc = EncryptionService(key_dir=str(tmp_path / "keys"))
    storage = StorageManager(
        encryption=enc,
        base_dir=str(tmp_path / "storage"),
    )
    return BackupManager(
        storage=storage,
        encryption=enc,
        backup_dir=str(tmp_path / "backups"),
    )


def test_backup_and_restore_config(backup_mgr, tmp_path):
    config_data = {"feature_flags": {"speech": True}, "model": "mamba-1.4b"}
    backup_path = backup_mgr.backup_config(config_data)
    assert pathlib.Path(backup_path).exists()
    restored = backup_mgr.restore_config(backup_path)
    assert restored["model"] == "mamba-1.4b"
    assert restored["feature_flags"]["speech"] is True


def test_backup_creates_encrypted_file(backup_mgr, tmp_path):
    data = {"key": "value", "nested": {"a": 1}}
    path = backup_mgr.backup_config(data)
    raw = pathlib.Path(path).read_bytes()
    # Should NOT be valid JSON if properly encrypted
    try:
        json.loads(raw)
        raise AssertionError("Backup file is not encrypted")
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass  # Expected: raw bytes are ciphertext


def test_list_backups(backup_mgr):
    backup_mgr.backup_config({"v": 1})
    backup_mgr.backup_config({"v": 2})
    listing = backup_mgr.list_backups()
    assert len(listing) >= 2
