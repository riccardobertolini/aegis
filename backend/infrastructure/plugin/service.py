"""PluginService — implements IPluginPort."""
from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Optional

from backend.domain.ports.plugin import (
    IPluginPort,
    PluginCallResult,
    PluginManifest,
    PluginStatus,
)
from backend.infrastructure.plugin.manifest import (
    ManifestError,
    load_manifest,
    verify_entry_checksum,
    verify_manifest_signature,
)
from backend.infrastructure.plugin.registry import PluginRegistry
from backend.infrastructure.plugin.sandbox import PluginSandbox
from backend.shared.logging import get_logger

logger = get_logger(__name__)


class PluginService(IPluginPort):
    """
    Full plugin lifecycle manager.

    plugins_root layout::

        plugins/
            my-plugin/
                aegis_plugin.json   # manifest
                main.py             # entry_point
                data/               # plugin's own data dir (read-only sandbox)
            plugin_registry.json    # auto-managed
    """

    def __init__(self, plugins_root: Path, signing_key: bytes | None = None):
        self._root = plugins_root
        self._root.mkdir(parents=True, exist_ok=True)
        self._registry = PluginRegistry(plugins_root)
        self._signing_key = signing_key  # None → signature check skipped
        self._sandboxes: dict[str, PluginSandbox] = {}

    # ------------------------------------------------------------------
    # Install / Uninstall
    # ------------------------------------------------------------------

    async def install(self, plugin_dir: str) -> PluginManifest:
        src = Path(plugin_dir).resolve()
        if not src.is_dir():
            raise FileNotFoundError(f"Plugin directory not found: {src}")

        manifest = load_manifest(src)  # validates permissions + entry_point

        if self._signing_key and not verify_manifest_signature(manifest, self._signing_key):
            raise PermissionError(
                f"Plugin '{manifest.plugin_id}' signature verification failed. "
                "Only signed plugins are accepted when a signing key is configured."
            )

        dest = self._root / manifest.plugin_id
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)

        # Re-load manifest from destination (checksum of copied files)
        installed_manifest = load_manifest(dest)
        installed_manifest.signature = manifest.signature
        self._registry.register(installed_manifest)
        logger.info("plugin.installed", plugin_id=manifest.plugin_id, version=manifest.version)
        return installed_manifest

    async def uninstall(self, plugin_id: str) -> None:
        await self.unload(plugin_id)
        dest = self._root / plugin_id
        if dest.exists():
            shutil.rmtree(dest)
        self._registry.remove(plugin_id)
        logger.info("plugin.uninstalled", plugin_id=plugin_id)

    # ------------------------------------------------------------------
    # Load / Unload
    # ------------------------------------------------------------------

    async def load(self, plugin_id: str) -> PluginManifest:
        manifest = self._registry.get(plugin_id)
        if not manifest:
            raise KeyError(f"Plugin '{plugin_id}' not installed.")
        if not await self.verify_integrity(plugin_id):
            raise PermissionError(
                f"Integrity check failed for plugin '{plugin_id}'. "
                "The entry_point file may have been tampered with."
            )
        plugin_dir = self._root / plugin_id
        sandbox = PluginSandbox(
            plugin_dir=plugin_dir,
            entry_point=manifest.entry_point,
            permissions=manifest.permissions,
            data_dir=plugin_dir / "data",
        )
        sandbox.load()
        self._sandboxes[plugin_id] = sandbox
        self._registry.set_status(plugin_id, PluginStatus.ACTIVE)
        logger.info("plugin.loaded", plugin_id=plugin_id)
        return manifest

    async def unload(self, plugin_id: str) -> None:
        self._sandboxes.pop(plugin_id, None)
        self._registry.set_status(plugin_id, PluginStatus.INACTIVE)
        logger.info("plugin.unloaded", plugin_id=plugin_id)

    # ------------------------------------------------------------------
    # Enable / Disable
    # ------------------------------------------------------------------

    async def enable(self, plugin_id: str) -> None:
        await self.load(plugin_id)

    async def disable(self, plugin_id: str) -> None:
        await self.unload(plugin_id)

    # ------------------------------------------------------------------
    # Call
    # ------------------------------------------------------------------

    async def call(
        self, plugin_id: str, method: str, payload: dict
    ) -> PluginCallResult:
        sandbox = self._sandboxes.get(plugin_id)
        if sandbox is None:
            raise RuntimeError(
                f"Plugin '{plugin_id}' is not loaded. Call enable() first."
            )
        start = time.perf_counter()
        try:
            result = sandbox.call(method, payload)
            elapsed = (time.perf_counter() - start) * 1000
            return PluginCallResult(
                plugin_id=plugin_id,
                method=method,
                result=result,
                elapsed_ms=round(elapsed, 2),
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("plugin.call.error", plugin_id=plugin_id, method=method, error=str(exc))
            return PluginCallResult(
                plugin_id=plugin_id,
                method=method,
                result={},
                elapsed_ms=round(elapsed, 2),
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def list_plugins(self) -> list[PluginManifest]:
        return self._registry.all()

    async def get_manifest(self, plugin_id: str) -> Optional[PluginManifest]:
        return self._registry.get(plugin_id)

    async def verify_integrity(self, plugin_id: str) -> bool:
        manifest = self._registry.get(plugin_id)
        if not manifest:
            return False
        plugin_dir = self._root / plugin_id
        return verify_entry_checksum(plugin_dir, manifest)
