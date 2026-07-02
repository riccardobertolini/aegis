"""Async SQLite engine factory (aiosqlite + SQLModel)."""
from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from backend.shared.config import get_settings

_engine = None
_session_factory = None


def _db_url() -> str:
    settings = get_settings()
    db_path: Path = Path(settings.data_dir) / "aegis.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{db_path}"


async def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _db_url(),
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return _engine


async def get_session_factory():
    global _session_factory
    if _session_factory is None:
        engine = await get_engine()
        _session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = await get_session_factory()
    async with factory() as session:
        yield session


async def create_all_tables() -> None:
    """Create all tables (used for tests and initial setup without Alembic)."""
    engine = await get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
