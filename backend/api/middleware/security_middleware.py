"""Security middleware: Bearer token extraction + hardening response headers."""
from __future__ import annotations

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

log = structlog.get_logger(__name__)

# Security response headers (OWASP hardening baseline)
_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",  # modern browsers rely on CSP
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    ),
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    # HSTS omitted intentionally: not applicable to air-gapped/HTTP-only deployments
}

# Paths that are completely public (no token check)
_PUBLIC_PATHS: frozenset[str] = frozenset([
    "/security/login",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
])


class SecurityMiddleware(BaseHTTPMiddleware):
    """Adds security response headers to every response.

    Token validation itself is handled by FastAPI ``Depends`` in each router.
    This middleware only adds hardening headers and logs suspicious patterns.
    """

    def __init__(self, app: ASGIApp, *, debug: bool = False) -> None:
        super().__init__(app)
        self._debug = debug

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        # Log every inbound request at DEBUG level (no sensitive data)
        log.debug(
            "http.request",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        response: Response = await call_next(request)

        # Inject security headers
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value

        # Remove server banner
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)

        # Log 4xx/5xx
        if response.status_code >= 400:
            log.warning(
                "http.response_error",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
            )

        return response
