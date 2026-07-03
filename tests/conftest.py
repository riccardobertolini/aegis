"""Shared pytest fixtures for all test suites.

All fixtures are air-gapped: no network calls, no cloud services.
In-memory SQLite is used for DB isolation.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Register all models before any test runs
import backend.domain.models  # noqa: F401
from backend.infrastructure.adapters.backup_manager import BackupManager
from backend.infrastructure.adapters.config_manager import ConfigManager
from backend.infrastructure.adapters.encryption import EncryptionService
from backend.infrastructure.adapters.storage import StorageManager

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Fresh in-memory SQLite session per test function."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------

@pytest.fixture
def encryption(tmp_path):
    """EncryptionService with per-test temporary key directory."""
    return EncryptionService(key_dir=str(tmp_path / "keys"))


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

@pytest.fixture
def storage(tmp_path, encryption):
    """StorageManager rooted in a temp directory."""
    return StorageManager(
        encryption=encryption,
        base_dir=str(tmp_path / "storage"),
    )


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

@pytest.fixture
def backup_manager(tmp_path, storage, encryption):
    """BackupManager using temp directories."""
    return BackupManager(
        storage=storage,
        encryption=encryption,
        backup_dir=str(tmp_path / "backups"),
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@pytest.fixture
def config_manager(tmp_path, encryption):
    """ConfigManager with isolated temp config directory."""
    return ConfigManager(
        encryption=encryption,
        config_dir=str(tmp_path / "config"),
    )
