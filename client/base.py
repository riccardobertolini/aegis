"""Base HTTP client for Aegis REST API."""
from __future__ import annotations

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"


class AegisClient:
    """Thin synchronous + async wrapper around the Aegis backend.

    Usage (sync)::

        client = AegisClient()
        print(client.health())

    Usage (async)::

        async with AegisClient.async_context() as client:
            print(await client.async_health())
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, token: str | None = None, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._headers: dict[str, str] = {"Accept": "application/json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    # ── sync helpers ──────────────────────────────────────────────────────────

    def _sync(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, headers=self._headers, timeout=self._timeout)

    def _get(self, path: str, **params) -> dict:
        with self._sync() as c:
            r = c.get(path, params=params)
            r.raise_for_status()
            return r.json()

    def _post(self, path: str, json: dict | None = None, **params) -> dict:
        with self._sync() as c:
            r = c.post(path, json=json, params=params)
            r.raise_for_status()
            return r.json()

    def _delete(self, path: str, **params) -> None:
        with self._sync() as c:
            r = c.delete(path, params=params)
            r.raise_for_status()

    # ── async helpers ─────────────────────────────────────────────────────────

    def _async(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, headers=self._headers, timeout=self._timeout)

    @classmethod
    def async_context(cls, **kwargs) -> httpx.AsyncClient:
        """Return an async context manager pre-configured with the client settings."""
        inst = cls(**kwargs)
        return inst._async()

    # ── system ────────────────────────────────────────────────────────────────

    def health(self) -> dict:
        """GET /health"""
        return self._get("/health")

    async def async_health(self) -> dict:
        async with self._async() as c:
            r = await c.get("/health")
            r.raise_for_status()
            return r.json()
