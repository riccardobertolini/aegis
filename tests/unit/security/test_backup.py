"""Unit tests: encrypted backup / restore."""
from pathlib import Path

import pytest

from backend.infrastructure.security.backup import BackupService


@pytest.fixture
def svc():
    return BackupService(passphrase="test-backup-passphrase")


def test_backup_creates_aeb_file(svc, tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "data.txt").write_text("sensitive")
    dest = tmp_path / "backups"
    dest.mkdir()
    path = svc.create(str(src), str(dest))
    assert Path(path).suffix == ".aeb"
    assert Path(path).exists()


def test_backup_restore_roundtrip(svc, tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "secret.txt").write_text("top secret content")
    dest_backup = tmp_path / "backups"
    dest_backup.mkdir()
    backup_path = svc.create(str(src), str(dest_backup))

    restore_dir = tmp_path / "restored"
    restore_dir.mkdir()
    svc.restore(backup_path, str(restore_dir))
    restored = restore_dir / "backup" / "secret.txt"
    assert restored.read_text() == "top secret content"


def test_wrong_passphrase_fails(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "f.txt").write_text("data")
    dest = tmp_path / "bk"
    dest.mkdir()
    svc1 = BackupService("correct")
    path = svc1.create(str(src), str(dest))
    svc2 = BackupService("wrong")
    with pytest.raises(Exception):
        svc2.restore(path, str(tmp_path / "out"))


def test_invalid_magic_raises(tmp_path):
    fake = tmp_path / "fake.aeb"
    fake.write_bytes(b"NOTVALID" + b"x" * 100)
    svc = BackupService("pw")
    with pytest.raises(ValueError, match="valid Aegis backup"):
        svc.restore(str(fake), str(tmp_path))
