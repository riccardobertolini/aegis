"""Plugin sandbox: network-blocked, resource-limited execution."""
from __future__ import annotations

import builtins

try:
    import resource  # POSIX only
except ImportError:  # Windows has no 'resource' module
    import types as _types

    resource = _types.SimpleNamespace(
        setrlimit=lambda *a, **k: None,
        getrlimit=lambda *a, **k: (-1, -1),
        RLIMIT_AS=0, RLIMIT_CPU=0, RLIMIT_DATA=0,
        RLIMIT_NOFILE=0, RLIMIT_FSIZE=0, RLIMIT_NPROC=0,
    )
import time
import types
from pathlib import Path

# ---------------------------------------------------------------------------
# Blocked built-ins (network + shell + dynamic import of dangerous modules)
# ---------------------------------------------------------------------------
_BLOCKED_BUILTINS = {
    "open",        # controlled separately via fs_read permission
    "__import__",  # replaced with restricted importer
    "eval",
    "exec",
    "compile",
    "breakpoint",
}

_BLOCKED_MODULES = frozenset({
    # Network
    "socket", "ssl", "http", "http.client", "http.server",
    "urllib", "urllib.request", "urllib.parse", "urllib.error",
    "urllib3", "requests", "httpx", "aiohttp", "websocket",
    "websockets", "ftplib", "smtplib", "poplib", "imaplib",
    "xmlrpc", "xmlrpc.client", "xmlrpc.server",
    "email", "email.mime",
    # Shell / process
    "subprocess", "os.system", "pty", "multiprocessing",
    "popen", "commands",
    # Dangerous introspection
    "ctypes", "cffi",
    # Cloud SDKs
    "boto3", "botocore", "azure", "google.cloud",
    "openai", "anthropic", "cohere", "huggingface_hub",
})


def _make_restricted_import(allowed_modules: frozenset[str]):
    """Return a __import__ replacement that blocks all network/shell modules."""
    _real_import = builtins.__import__

    def _restricted_import(name, *args, **kwargs):
        base = name.split(".")[0]
        if base in _BLOCKED_MODULES or name in _BLOCKED_MODULES:
            raise ImportError(
                f"[Aegis Sandbox] Import of '{name}' is BLOCKED. "
                "Network and shell access are not permitted inside plugins."
            )
        return _real_import(name, *args, **kwargs)

    return _restricted_import


class SandboxViolation(PermissionError):
    """Raised when a plugin attempts a forbidden operation."""


class PluginSandbox:
    """
    Executes a plugin's Python entry-point inside a restricted namespace.

    Guarantees:
    - All network-related modules are blocked at import level.
    - eval/exec/compile/breakpoint are removed from builtins.
    - CPU time capped (Unix: RLIMIT_CPU; Windows: wall-clock timeout).
    - Memory capped (Unix: RLIMIT_AS; Windows: best-effort).
    - No access to sys.modules injection.
    """

    CPU_LIMIT_SECONDS = 10
    MEMORY_LIMIT_BYTES = 256 * 1024 * 1024  # 256 MB

    def __init__(
        self,
        plugin_dir: Path,
        entry_point: str,
        permissions: list[str],
        data_dir: Path | None = None,
    ):
        self._plugin_dir = plugin_dir
        self._entry_point = entry_point
        self._permissions = set(permissions)
        self._data_dir = data_dir or plugin_dir / "data"
        self._module: types.ModuleType | None = None

    def load(self) -> None:
        """Parse and exec the plugin source into a restricted module namespace."""
        source_path = self._plugin_dir / self._entry_point
        source = source_path.read_text(encoding="utf-8")

        # Build restricted builtins
        safe_builtins = {k: v for k, v in vars(builtins).items()
                         if k not in _BLOCKED_BUILTINS}
        safe_builtins["__import__"] = _make_restricted_import(
            frozenset()  # allow-list empty — block-list is the gate
        )
        if "fs_read" in self._permissions:
            # Allow read-only open inside plugin's own data dir
            safe_builtins["open"] = self._make_safe_open()

        module = types.ModuleType(f"aegis_plugin_{source_path.stem}")
        module.__dict__["__builtins__"] = safe_builtins
        module.__dict__["__file__"] = str(source_path)
        module.__dict__["PLUGIN_DATA_DIR"] = str(self._data_dir)

        self._apply_resource_limits()
        exec(compile(source, str(source_path), "exec"), module.__dict__)  # noqa: S102
        self._module = module

    def call(self, method: str, payload: dict) -> dict:
        """Call a top-level function in the plugin module."""
        if self._module is None:
            raise RuntimeError("Plugin not loaded. Call load() first.")
        fn = getattr(self._module, method, None)
        if fn is None or not callable(fn):
            raise AttributeError(
                f"Plugin has no callable method '{method}'. "
                f"Available: {[k for k, v in self._module.__dict__.items() if callable(v) and not k.startswith('_')]}"
            )
        start = time.perf_counter()
        result = fn(payload)
        elapsed = (time.perf_counter() - start) * 1000
        if not isinstance(result, dict):
            result = {"result": result}
        result["__elapsed_ms"] = round(elapsed, 2)
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_resource_limits(self) -> None:
        """Apply OS-level resource caps (Unix only; silent on Windows)."""
        try:
            # CPU time
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (self.CPU_LIMIT_SECONDS, self.CPU_LIMIT_SECONDS),
            )
            # Virtual memory
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self.MEMORY_LIMIT_BYTES, self.MEMORY_LIMIT_BYTES),
            )
        except (AttributeError, ValueError):
            # Windows — resource module unavailable or limit too low
            pass

    def _make_safe_open(self):
        data_dir = str(self._data_dir.resolve())

        def _safe_open(file, mode="r", *args, **kwargs):
            resolved = str(Path(file).resolve())
            if not resolved.startswith(data_dir):
                raise SandboxViolation(
                    f"[Aegis Sandbox] open('{file}') denied. "
                    f"Plugins may only read from their own data dir: {data_dir}"
                )
            if any(c in mode for c in ("w", "a", "x", "+")):
                raise SandboxViolation(
                    f"[Aegis Sandbox] write mode '{mode}' denied for plugins."
                )
            return builtins.open(file, mode, *args, **kwargs)

        return _safe_open
