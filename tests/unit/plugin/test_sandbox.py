"""Sandbox tests: verify network access is BLOCKED, and safe ops work."""
import sys
import textwrap
from pathlib import Path

import pytest

from backend.infrastructure.plugin.sandbox import PluginSandbox, SandboxViolation


def _write_plugin(tmp_path: Path, code: str, name: str = "main.py") -> Path:
    plugin_dir = tmp_path / "test_plugin"
    plugin_dir.mkdir()
    (plugin_dir / name).write_text(textwrap.dedent(code), encoding="utf-8")
    return plugin_dir


# ---------------------------------------------------------------------------
# Network blocking tests
# ---------------------------------------------------------------------------

def test_socket_import_blocked(tmp_path):
    """Plugin MUST NOT import socket."""
    plugin_dir = _write_plugin(tmp_path, """
        import socket
        def run(payload):
            return {}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    with pytest.raises(ImportError, match="BLOCKED"):
        sandbox.load()


def test_requests_import_blocked(tmp_path):
    """Plugin MUST NOT import requests."""
    plugin_dir = _write_plugin(tmp_path, """
        import requests
        def run(payload):
            return {}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    with pytest.raises(ImportError, match="BLOCKED"):
        sandbox.load()


def test_urllib_import_blocked(tmp_path):
    """Plugin MUST NOT import urllib."""
    plugin_dir = _write_plugin(tmp_path, """
        import urllib.request
        def run(payload):
            return {}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    with pytest.raises(ImportError, match="BLOCKED"):
        sandbox.load()


def test_httpx_import_blocked(tmp_path):
    """Plugin MUST NOT import httpx."""
    plugin_dir = _write_plugin(tmp_path, """
        import httpx
        def run(payload):
            return {}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    with pytest.raises(ImportError, match="BLOCKED"):
        sandbox.load()


def test_subprocess_import_blocked(tmp_path):
    """Plugin MUST NOT import subprocess."""
    plugin_dir = _write_plugin(tmp_path, """
        import subprocess
        def run(payload):
            return {}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    with pytest.raises(ImportError, match="BLOCKED"):
        sandbox.load()


def test_eval_blocked(tmp_path):
    """eval() must be removed from builtins."""
    plugin_dir = _write_plugin(tmp_path, """
        def run(payload):
            return {"result": eval("1+1")}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    sandbox.load()
    with pytest.raises((NameError, TypeError)):
        sandbox.call("run", {})


def test_exec_blocked(tmp_path):
    """exec() must be removed from builtins."""
    plugin_dir = _write_plugin(tmp_path, """
        def run(payload):
            exec("x=1")
            return {}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    sandbox.load()
    with pytest.raises((NameError, TypeError)):
        sandbox.call("run", {})


# ---------------------------------------------------------------------------
# Safe operation tests
# ---------------------------------------------------------------------------

def test_safe_math_works(tmp_path):
    """Pure math plugins must execute correctly."""
    plugin_dir = _write_plugin(tmp_path, """
        def add(payload):
            return {"sum": payload["a"] + payload["b"]}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    sandbox.load()
    result = sandbox.call("add", {"a": 3, "b": 4})
    assert result["sum"] == 7


def test_json_import_allowed(tmp_path):
    """Standard library json is allowed (not a network module)."""
    plugin_dir = _write_plugin(tmp_path, """
        import json
        def run(payload):
            return {"encoded": json.dumps(payload)}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    sandbox.load()
    result = sandbox.call("run", {"key": "val"})
    assert "encoded" in result


def test_fs_read_outside_data_dir_blocked(tmp_path):
    """fs_read permission must not allow reads outside plugin data dir."""
    plugin_dir = _write_plugin(tmp_path, """
        def run(payload):
            with open("/etc/passwd", "r") as f:
                return {"content": f.read()}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=["fs_read"])
    sandbox.load()
    with pytest.raises(SandboxViolation):
        sandbox.call("run", {})


def test_unknown_method_raises(tmp_path):
    """Calling a non-existent method raises AttributeError."""
    plugin_dir = _write_plugin(tmp_path, """
        def run(payload):
            return {}
    """)
    sandbox = PluginSandbox(plugin_dir, "main.py", permissions=[])
    sandbox.load()
    with pytest.raises(AttributeError):
        sandbox.call("nonexistent", {})
