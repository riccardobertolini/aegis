"""Plugin manifest loading and integrity verification."""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.domain.ports.plugin import (
    ALLOWED_PERMISSIONS,
    DENIED_PERMISSIONS,
    PluginManifest,
    PluginStatus,
)


class ManifestError(ValueError):
    pass


def load_manifest(plugin_dir: Path) -> PluginManifest:
    """
    Load and validate aegis_plugin.json from plugin_dir.
    Required fields: plugin_id, name, version, entry_point.
    Rejects any manifest that requests denied permissions.
    """
    manifest_path = plugin_dir / "aegis_plugin.json"
    if not manifest_path.exists():
        raise ManifestError(f"Missing aegis_plugin.json in {plugin_dir}")

    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Invalid JSON in aegis_plugin.json: {exc}") from exc

    for required in ("plugin_id", "name", "version"):
        if not data.get(required):
            raise ManifestError(f"aegis_plugin.json missing required field: {required}")

    permissions: list[str] = data.get("permissions", [])
    bad = [p for p in permissions if p in DENIED_PERMISSIONS]
    if bad:
        raise ManifestError(
            f"Plugin '{data['plugin_id']}' requests forbidden permissions: {bad}. "
            "Network access and shell execution are never allowed."
        )
    unknown = [p for p in permissions if p not in ALLOWED_PERMISSIONS]
    if unknown:
        raise ManifestError(
            f"Plugin '{data['plugin_id']}' requests unknown permissions: {unknown}. "
            f"Allowed: {sorted(ALLOWED_PERMISSIONS)}"
        )

    entry_point = data.get("entry_point", "main.py")
    entry_path = plugin_dir / entry_point
    if not entry_path.exists():
        raise ManifestError(
            f"entry_point '{entry_point}' not found in {plugin_dir}"
        )

    checksum = _sha256_file(entry_path)

    return PluginManifest(
        plugin_id=data["plugin_id"],
        name=data["name"],
        version=data["version"],
        description=data.get("description", ""),
        author=data.get("author", ""),
        permissions=permissions,
        entry_point=entry_point,
        signature=data.get("signature"),
        checksum=checksum,
        installed_at=datetime.now(timezone.utc),
        status=PluginStatus.INACTIVE,
    )


def verify_manifest_signature(manifest: PluginManifest, secret_key: bytes) -> bool:
    """
    Verify the manifest signature.
    Signature = HMAC-SHA256(secret_key, canonical_json) encoded as hex.
    canonical_json = JSON of {plugin_id, name, version, permissions, entry_point} sorted keys.
    """
    if not manifest.signature:
        return False
    canonical = json.dumps(
        {
            "plugin_id": manifest.plugin_id,
            "name": manifest.name,
            "version": manifest.version,
            "permissions": sorted(manifest.permissions),
            "entry_point": manifest.entry_point,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    expected = hmac.new(secret_key, canonical, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, manifest.signature)


def verify_entry_checksum(plugin_dir: Path, manifest: PluginManifest) -> bool:
    """Re-compute SHA-256 of entry_point and compare against stored checksum."""
    if not manifest.checksum:
        return False
    entry_path = plugin_dir / manifest.entry_point
    if not entry_path.exists():
        return False
    return hmac.compare_digest(manifest.checksum, _sha256_file(entry_path))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sign_manifest(manifest: PluginManifest, secret_key: bytes) -> str:
    """Generate HMAC-SHA256 signature for a manifest. Used at install time."""
    canonical = json.dumps(
        {
            "plugin_id": manifest.plugin_id,
            "name": manifest.name,
            "version": manifest.version,
            "permissions": sorted(manifest.permissions),
            "entry_point": manifest.entry_point,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hmac.new(secret_key, canonical, hashlib.sha256).hexdigest()
