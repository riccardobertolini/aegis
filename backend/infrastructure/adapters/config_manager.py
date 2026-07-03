"""ConfigManager — offline-first configuration with per-assistant overrides.

Storage
-------
config/
  global.json.enc        <- global config (AES-256-GCM encrypted JSON)
  assistant.<id>.json.enc <- per-assistant overrides

Key lookup order
----------------
  get_for_assistant(key, assistant_id)
    1. assistant.<id> override
    2. global config
    3. None (caller decides default)

All reads/writes are synchronous; config is small and in-process.
No network I/O ever performed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.infrastructure.adapters.encryption import EncryptionService

_CONFIG_DIR = Path("config")
_GLOBAL_FILE = "global.json.enc"


class ConfigManager:
    """Encrypted local configuration store with feature-flag support."""

    def __init__(
        self,
        encryption: EncryptionService,
        config_dir: str | Path = _CONFIG_DIR,
    ) -> None:
        self._enc = encryption
        self._dir = Path(config_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._global: dict[str, Any] = {}
        self._assistant_overrides: dict[str, dict[str, Any]] = {}
        self.load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _global_path(self) -> Path:
        return self._dir / _GLOBAL_FILE

    def _assistant_path(self, assistant_id: str) -> Path:
        return self._dir / f"assistant.{assistant_id}.json.enc"

    def load(self) -> None:
        """Load (decrypt) config from disk.  No-op if files don't exist yet."""
        p = self._global_path()
        if p.exists():
            self._global = json.loads(self._enc.decrypt_str(p.read_text()))
        for path in self._dir.glob("assistant.*.json.enc"):
            aid = path.stem.split(".", 1)[1].replace(".json", "")
            self._assistant_overrides[aid] = json.loads(
                self._enc.decrypt_str(path.read_text())
            )

    def save(self) -> None:
        """Encrypt and persist current config to disk."""
        self._global_path().write_text(
            self._enc.encrypt_str(json.dumps(self._global))
        )
        for aid, data in self._assistant_overrides.items():
            self._assistant_path(aid).write_text(
                self._enc.encrypt_str(json.dumps(data))
            )

    # ------------------------------------------------------------------
    # Global get / set
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Dot-notation key lookup in global config (e.g. ``global.model_name``)."""
        parts = key.split(".")
        node: Any = self._global
        for part in parts:
            if not isinstance(node, dict):
                return default
            node = node.get(part)
            if node is None:
                return default
        return node

    def set(self, key: str, value: Any) -> None:
        """Dot-notation key set in global config; creates intermediate dicts."""
        parts = key.split(".")
        node = self._global
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    # ------------------------------------------------------------------
    # Per-assistant overrides
    # ------------------------------------------------------------------

    def get_for_assistant(
        self, key: str, assistant_id: str, default: Any = None
    ) -> Any:
        """Look up *key* with assistant override > global > default."""
        overrides = self._assistant_overrides.get(assistant_id, {})
        parts = key.split(".")
        # Check assistant override first (strip leading 'assistant.' if present)
        stripped = parts[1:] if parts[0] == "assistant" else parts
        node: Any = overrides
        for part in stripped:
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(part)
        if node is not None:
            return node
        # Fallback to global
        value = self.get(key, None)
        if value is None and "." in key:
            head, tail = key.split(".", 1)
            value = self.get(f"{head}.{assistant_id}.{tail}", None)
        return default if value is None else value

    def set_for_assistant(self, key: str, assistant_id: str, value: Any) -> None:
        overrides = self._assistant_overrides.setdefault(assistant_id, {})
        parts = key.split(".")
        node = overrides
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    # ------------------------------------------------------------------
    # Feature flags
    # ------------------------------------------------------------------

    def feature_enabled(self, feature: str, assistant_id: str | None = None) -> bool:
        if assistant_id:
            return bool(
                self.get_for_assistant(
                    f"feature_flags.{feature}", assistant_id, False
                )
            )
        flags = self._global.get("feature_flags", {})
        return bool(flags.get(feature, False))

    def enable_feature(self, feature: str) -> None:
        flags = self._global.setdefault("feature_flags", {})
        flags[feature] = True

    def disable_feature(self, feature: str) -> None:
        flags = self._global.setdefault("feature_flags", {})
        flags[feature] = False

    # ------------------------------------------------------------------
    # Export / import (plain JSON — for backup use only)
    # ------------------------------------------------------------------

    def export_plain(self) -> dict[str, Any]:
        """Return a plain-Python dict (for backup serialisation)."""
        return {
            "global": self._global,
            "assistant_overrides": self._assistant_overrides,
        }

    def import_plain(self, data: dict[str, Any]) -> None:
        """Restore from a plain-Python dict (from a backup restore)."""
        self._global = data.get("global", {})
        self._assistant_overrides = data.get("assistant_overrides", {})
        self.save()
