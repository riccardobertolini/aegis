"""Async SQLite engine factory.

Creates a single shared async engine pointing to the local SQLite file
defined in Settings.database_url (e.g. sqlite+aiosqlite:///./data/aegis.db).
No remote connections, no cloud DB — air-gapped by design.
"""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.shared.config import get_settings


@lru_cache(maxsize=1)
def get_engine():
    """Return the singleton async engine (cached after first call)."""
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
    )
    return engine


async def create_all_tables() -> None:
    """Create all SQLModel tables (used for tests / first-run bootstrap)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


def get_async_session_factory():
    """Return a configured async session factory."""
    return sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency: yields a database session per request."""
    factory = get_async_session_factory()
    async with factory() as session:
        yield session
