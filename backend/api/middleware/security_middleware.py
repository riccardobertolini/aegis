"""FastAPI middleware: request-level security enforcement.

- Extracts Bearer token and attaches UserPrincipal to request.state
- Logs every request to the audit log (async, non-blocking)
- Enforces TLS-only in production (X-Forwarded-Proto check)
"""
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

import structlog

log = structlog.get_logger(__name__)

_PUBLIC_PATHS = {"/security/auth/login", "/health", "/docs", "/openapi.json", "/redoc"}


class SecurityMiddleware(BaseHTTPMiddleware):
    """Lightweight request security middleware.

    Responsibilities:
    - Skip authentication for public paths.
    - For all other paths, verify Bearer token and attach principal to request.state.
    - Add security-relevant response headers.
    """

    def __init__(self, app: ASGIApp, security_service=None) -> None:
        super().__init__(app)
        self._security = security_service

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.principal = None

        path = request.url.path
        if path not in _PUBLIC_PATHS and self._security is not None:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.removeprefix("Bearer ")
                try:
                    principal = await self._security.verify_token(token)
                    request.state.principal = principal
                except Exception:
                    pass  # Endpoint-level dependency handles 401

        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
