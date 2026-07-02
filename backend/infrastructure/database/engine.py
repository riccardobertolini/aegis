"""Async SQLite engine factory — canonical, air-gapped, zero server.

Single source of truth for the async engine, session factory, and
FastAPI dependency.  All other modules import from here.

URL format:  sqlite+aiosqlite:///./data/aegis.db
No remote connections, no cloud DB, no telemetry.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.shared.config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Singleton async engine — created once, reused for the lifetime of the process."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def _session_factory() -> sessionmaker:  # type: ignore[type-arg]
    return sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields one session per request, auto-committed on success."""
    async with _session_factory()() as session:  # type: ignore[operator]
        yield session


# Alias consumed by Fase 6 security layer
get_async_session = get_session


def get_async_session_factory():
    """Return a callable context-manager that yields an AsyncSession.

    Used by AdministrationService and other services that manage their own
    session lifecycle (i.e. not FastAPI dependency-injected).
    """
    @asynccontextmanager
    async def _factory():
        async with _session_factory()() as session:  # type: ignore[operator]
            yield session

    return _factory


async def create_all_tables() -> None:
    """Bootstrap helper: create all SQLModel tables.

    Used only for test fixtures and first-run setup.
    Production runs use Alembic migrations (see infrastructure/migrations/).
    """
    # Import models so SQLModel.metadata is populated before create_all.
    import backend.infrastructure.database.models  # noqa: F401
    import backend.infrastructure.administration.models  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_all_tables() -> None:
    """Test helper only — never call in production."""
    import backend.infrastructure.database.models  # noqa: F401
    import backend.infrastructure.administration.models  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
