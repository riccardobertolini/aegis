"""Alembic env.py — air-gapped, async SQLite migrations.

Run migrations:
    alembic upgrade head

Create a new migration:
    alembic revision --autogenerate -m "describe_change"

No remote DB, no cloud, no internet required.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Import all models so their metadata is registered before autogenerate
import backend.infrastructure.database.models  # noqa: F401
from backend.shared.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def get_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(get_url(), echo=False)
    async with engine.connect() as connection:
        await connection.run_sync(
            lambda sync_conn: context.configure(
                connection=sync_conn,
                target_metadata=target_metadata,
                render_as_batch=True,  # required for SQLite ALTER TABLE support
            )
        )
        async with connection.begin():
            await connection.run_sync(lambda _: context.run_migrations())
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
