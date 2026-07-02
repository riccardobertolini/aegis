"""BackupManager — encrypted local backup and restore.

Backup format (.aegbak)
-----------------------
AES-256-GCM encrypted blob whose plaintext is a UTF-8 JSON string:
{
  "version": 1,
  "created_at": "<ISO-8601>",
  "aegis_version": "0.2.0",
  "type": "config" | "full",
  "data": { ... }
}

No data ever leaves the local machine.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from backend.infrastructure.adapters.encryption import EncryptionService
from backend.infrastructure.adapters.storage import StorageManager

_BACKUP_DIR = Path("data/backups")
_AEGIS_VERSION = "0.2.0"


class BackupManager:
    """Creates and restores encrypted local backups."""

    def __init__(
        self,
        storage: StorageManager,
        encryption: EncryptionService,
        backup_dir: str | Path = _BACKUP_DIR,
    ) -> None:
        self._storage = storage
        self._enc = encryption
        self._backup_dir = Path(backup_dir)
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ts(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%dT%H_%M_%S")

    def _wrap(self, backup_type: str, data: Dict[str, Any]) -> bytes:
        payload = {
            "version": 1,
            "created_at": datetime.utcnow().isoformat(),
            "aegis_version": _AEGIS_VERSION,
            "type": backup_type,
            "data": data,
        }
        return self._enc.encrypt(json.dumps(payload).encode("utf-8"))

    def _unwrap(self, blob: bytes) -> Dict[str, Any]:
        plaintext = self._enc.decrypt(blob)
        return json.loads(plaintext.decode("utf-8"))

    def _write(self, name: str, blob: bytes) -> str:
        path = self._backup_dir / name
        path.write_bytes(blob)
        return str(path)

    # ------------------------------------------------------------------
    # Config backup / restore
    # ------------------------------------------------------------------

    def backup_config(self, config_data: Dict[str, Any]) -> str:
        """Encrypt and persist *config_data*; return the backup file path."""
        blob = self._wrap("config", config_data)
        return self._write(f"{self._ts()}_config.aegbak", blob)

    def restore_config(self, path: str) -> Dict[str, Any]:
        """Decrypt and return config data from a backup file."""
        blob = Path(path).read_bytes()
        envelope = self._unwrap(blob)
        return envelope["data"]

    # ------------------------------------------------------------------
    # Full backup / restore (DB + config)
    # ------------------------------------------------------------------

    def backup_full(self, db_dump: str, config_data: Dict[str, Any]) -> str:
        """Create a full backup containing both DB dump and config."""
        blob = self._wrap("full", {"db_dump": db_dump, "config": config_data})
        return self._write(f"{self._ts()}_full.aegbak", blob)

    def restore_full(self, path: str) -> Dict[str, Any]:
        blob = Path(path).read_bytes()
        envelope = self._unwrap(blob)
        return envelope["data"]

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_backups(self) -> List[Dict[str, Any]]:
        """Return metadata for all backup files in the backup directory."""
        result = []
        for p in sorted(self._backup_dir.glob("*.aegbak"), reverse=True):
            result.append({
                "filename": p.name,
                "path": str(p),
                "size_bytes": p.stat().st_size,
            })
        return result

    def purge_old_backups(self, keep: int = 10) -> int:
        """Delete oldest backups keeping the *keep* most recent. Returns count deleted."""
        files = sorted(self._backup_dir.glob("*.aegbak"), reverse=True)
        to_delete = files[keep:]
        for f in to_delete:
            f.unlink()
        return len(to_delete)
