"""LocalOnlyMiddleware — reject requests not coming from loopback.

Protects all /admin/* and /auth/* endpoints from LAN / remote access.
Deploy note: if Aegis runs behind a reverse proxy on the same host,
set AEGIS_TRUSTED_PROXIES=127.0.0.1 and use X-Forwarded-For.
"""
from __future__ import annotations

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

LOCAL_PREFIXES = ("/admin", "/auth")
LOOPBACK_NETS = ("127.", "::1", "0:0:0:0:0:0:0:1")


class LocalOnlyMiddleware(BaseHTTPMiddleware):
    """Block non-loopback clients from accessing protected paths."""

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in LOCAL_PREFIXES):
            client_ip = request.client.host if request.client else ""
            if not any(client_ip.startswith(p) for p in LOOPBACK_NETS):
                logger.warning(
                    "LocalOnlyMiddleware: blocked %s from %s",
                    request.url.path, client_ip,
                )
                return Response(
                    content='{"detail":"Access denied: localhost only"}',
                    status_code=403,
                    media_type="application/json",
                )
        return await call_next(request)
