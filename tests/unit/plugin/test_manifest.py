"""Unit tests — manifest loading and signing."""
import json
from pathlib import Path

import pytest

from backend.infrastructure.plugin.manifest import (
    ManifestError,
    load_manifest,
    sign_manifest,
    verify_entry_checksum,
    verify_manifest_signature,
)


def _make_plugin(tmp_path: Path, manifest: dict, code: str = "def run(p): return {}") -> Path:
    plugin_dir = tmp_path / manifest.get("plugin_id", "test-plugin")
    plugin_dir.mkdir()
    (plugin_dir / "aegis_plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    entry = manifest.get("entry_point", "main.py")
    (plugin_dir / entry).write_text(code, encoding="utf-8")
    return plugin_dir


def test_load_valid_manifest(tmp_path):
    d = _make_plugin(tmp_path, {
        "plugin_id": "my-plugin",
        "name": "My Plugin",
        "version": "1.0.0",
        "permissions": ["fs_read"],
    })
    m = load_manifest(d)
    assert m.plugin_id == "my-plugin"
    assert m.checksum is not None


def test_missing_manifest_raises(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    with pytest.raises(ManifestError, match="Missing"):
        load_manifest(d)


def test_denied_permission_raises(tmp_path):
    d = _make_plugin(tmp_path, {
        "plugin_id": "bad",
        "name": "Bad",
        "version": "1.0",
        "permissions": ["network"],
    })
    with pytest.raises(ManifestError, match="forbidden"):
        load_manifest(d)


def test_sign_and_verify(tmp_path):
    d = _make_plugin(tmp_path, {
        "plugin_id": "signed-plugin",
        "name": "Signed",
        "version": "1.0",
        "permissions": [],
    })
    m = load_manifest(d)
    key = b"super-secret-signing-key"
    sig = sign_manifest(m, key)
    m.signature = sig
    assert verify_manifest_signature(m, key) is True


def test_wrong_key_fails(tmp_path):
    d = _make_plugin(tmp_path, {
        "plugin_id": "signed-plugin",
        "name": "Signed",
        "version": "1.0",
        "permissions": [],
    })
    m = load_manifest(d)
    m.signature = sign_manifest(m, b"correct-key")
    assert verify_manifest_signature(m, b"wrong-key") is False


def test_checksum_tamper_detected(tmp_path):
    d = _make_plugin(tmp_path, {
        "plugin_id": "tamper-test",
        "name": "T",
        "version": "1.0",
        "permissions": [],
    })
    m = load_manifest(d)
    # Tamper the entry point after installation
    (d / "main.py").write_text("import socket  # injected!", encoding="utf-8")
    assert verify_entry_checksum(d, m) is False
