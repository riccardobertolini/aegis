"""PluginRegistry: persistent store of installed plugins (JSON file)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from backend.domain.ports.plugin import PluginManifest, PluginStatus

_REGISTRY_FILE = "plugin_registry.json"


class PluginRegistry:
    """
    Loads/saves plugin metadata to a JSON file inside plugins_root.
    Thread-safety: single-process only (fine for Aegis single-server model).
    """

    def __init__(self, plugins_root: Path):
        self._root = plugins_root
        self._path = plugins_root / _REGISTRY_FILE
        self._entries: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    self._entries = json.load(f)
            except Exception:
                self._entries = {}

    def _save(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, indent=2, default=str)

    def register(self, manifest: PluginManifest) -> None:
        self._entries[manifest.plugin_id] = {
            "plugin_id": manifest.plugin_id,
            "name": manifest.name,
            "version": manifest.version,
            "description": manifest.description,
            "author": manifest.author,
            "permissions": manifest.permissions,
            "entry_point": manifest.entry_point,
            "signature": manifest.signature,
            "checksum": manifest.checksum,
            "installed_at": manifest.installed_at.isoformat() if manifest.installed_at else None,
            "status": manifest.status.value,
        }
        self._save()

    def remove(self, plugin_id: str) -> None:
        self._entries.pop(plugin_id, None)
        self._save()

    def set_status(self, plugin_id: str, status: PluginStatus) -> None:
        if plugin_id in self._entries:
            self._entries[plugin_id]["status"] = status.value
            self._save()

    def get(self, plugin_id: str) -> PluginManifest | None:
        entry = self._entries.get(plugin_id)
        if not entry:
            return None
        return self._entry_to_manifest(entry)

    def all(self) -> list[PluginManifest]:
        return [self._entry_to_manifest(e) for e in self._entries.values()]

    @staticmethod
    def _entry_to_manifest(e: dict) -> PluginManifest:
        installed_at = None
        if e.get("installed_at"):
            try:
                installed_at = datetime.fromisoformat(e["installed_at"])
            except ValueError:
                pass
        return PluginManifest(
            plugin_id=e["plugin_id"],
            name=e["name"],
            version=e["version"],
            description=e.get("description", ""),
            author=e.get("author", ""),
            permissions=e.get("permissions", []),
            entry_point=e.get("entry_point", "main.py"),
            signature=e.get("signature"),
            checksum=e.get("checksum"),
            installed_at=installed_at,
            status=PluginStatus(e.get("status", "inactive")),
        )
