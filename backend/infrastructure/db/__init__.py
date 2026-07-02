"""Compatibility shim: re-export get_async_session for Fase 6 security layer.

Fase 6 (infrastructure/security/dependencies.py) imports:
    from backend.infrastructure.db import get_async_session

The canonical implementation lives in infrastructure/database/engine.py.
This shim ensures zero breaking changes across phases.
"""
from backend.infrastructure.database.engine import get_session as get_async_session

__all__ = ["get_async_session"]
