"""Tests for LocalOnlyMiddleware."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.api.middleware.localhost_only import LocalOnlyMiddleware


def _make_app():
    app = FastAPI()
    app.add_middleware(LocalOnlyMiddleware)

    @app.get("/admin/health")
    async def admin_health():
        return {"ok": True}

    @app.get("/public")
    async def public():
        return {"ok": True}

    return app


def test_loopback_allowed():
    app = _make_app()
    client = TestClient(app, base_url="http://127.0.0.1")
    # TestClient connects from 127.0.0.1 by default in starlette scope
    resp = client.get("/admin/health")
    # May get 503 if admin_service not wired — but NOT 403
    assert resp.status_code != 403


def test_public_always_allowed():
    app = _make_app()
    client = TestClient(app)
    resp = client.get("/public")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
