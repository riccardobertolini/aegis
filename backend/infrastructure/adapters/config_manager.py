"""Local SQLite-backed config manager with encryption support."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.ports.config_manager import IConfigManagerPort
from backend.domain.ports.encryption import IEncryptionPort
from backend.infrastructure.database.models import ConfigEntryModel
from backend.shared.exceptions import ConfigError

_GLOBAL_SCOPE = "global"


class SQLiteConfigManager(IConfigManagerPort):
    """Stores config in SQLite config_entries table; sensitive values are encrypted."""

    def __init__(self, session: AsyncSession, encryption: IEncryptionPort | None = None) -> None:
        self._session = session
        self._enc = encryption

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_entry(self, scope: str, key: str) -> ConfigEntryModel | None:
        stmt = select(ConfigEntryModel).where(
            ConfigEntryModel.scope == scope,
            ConfigEntryModel.key == key,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def _decode_value(self, entry: ConfigEntryModel) -> Any:
        raw = entry.value_json
        if entry.is_encrypted and self._enc:
            raw = self._enc.decrypt_str(raw)
        return json.loads(raw)

    async def _set_entry(self, scope: str, key: str, value: Any, encrypt: bool = False) -> None:
        raw = json.dumps(value)
        if encrypt and self._enc:
            raw = self._enc.encrypt_str(raw)
        entry = await self._get_entry(scope, key)
        now = datetime.now(tz=timezone.utc)
        if entry is None:
            entry = ConfigEntryModel(
                id=str(uuid.uuid4()), scope=scope, key=key,
                value_json=raw, is_encrypted=encrypt,
                created_at=now, updated_at=now,
            )
        else:
            entry.value_json = raw
            entry.is_encrypted = encrypt
            entry.updated_at = now
        await self._session.merge(entry)
        await self._session.commit()

    # ------------------------------------------------------------------
    # IConfigManagerPort
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        raise NotImplementedError("Use async get_async instead")

    def set(self, key: str, value: Any) -> None:
        raise NotImplementedError("Use async set_async instead")

    async def get_async(self, key: str, default: Any = None) -> Any:
        entry = await self._get_entry(_GLOBAL_SCOPE, key)
        if entry is None:
            return default
        return self._decode_value(entry)

    async def set_async(self, key: str, value: Any, encrypt: bool = False) -> None:
        await self._set_entry(_GLOBAL_SCOPE, key, value, encrypt=encrypt)

    async def get_assistant_override(self, assistant_id: str, key: str, default: Any = None) -> Any:
        entry = await self._get_entry(assistant_id, key)
        if entry is not None:
            return self._decode_value(entry)
        return await self.get_async(key, default)

    async def set_assistant_override(self, assistant_id: str, key: str, value: Any) -> None:
        await self._set_entry(assistant_id, key, value)

    async def delete_assistant_override(self, assistant_id: str, key: str) -> None:
        entry = await self._get_entry(assistant_id, key)
        if entry:
            await self._session.delete(entry)
            await self._session.commit()

    async def is_feature_enabled(self, flag: str, assistant_id: str | None = None) -> bool:
        key = f"feature_flag.{flag}"
        if assistant_id:
            return bool(await self.get_assistant_override(assistant_id, key, False))
        return bool(await self.get_async(key, False))

    async def set_feature_flag(self, flag: str, enabled: bool, assistant_id: str | None = None) -> None:
        key = f"feature_flag.{flag}"
        if assistant_id:
            await self.set_assistant_override(assistant_id, key, enabled)
        else:
            await self.set_async(key, enabled)

    async def export_config(self, path: str) -> None:
        """Export all config entries to an encrypted JSON file."""
        stmt = select(ConfigEntryModel)
        result = await self._session.execute(stmt)
        entries = result.scalars().all()
        data = [
            {
                "scope": e.scope, "key": e.key,
                "value_json": e.value_json, "is_encrypted": e.is_encrypted,
            }
            for e in entries
        ]
        raw = json.dumps(data, indent=2).encode()
        if self._enc:
            raw = self._enc.encrypt_bytes(raw)
        Path(path).write_bytes(raw)

    async def import_config(self, path: str) -> None:
        """Import config from an encrypted JSON file."""
        raw = Path(path).read_bytes()
        if self._enc:
            raw = self._enc.decrypt_bytes(raw)
        entries = json.loads(raw.decode())
        now = datetime.now(tz=timezone.utc)
        for e in entries:
            existing = await self._get_entry(e["scope"], e["key"])
            if existing is None:
                await self._session.merge(ConfigEntryModel(
                    id=str(uuid.uuid4()),
                    scope=e["scope"], key=e["key"],
                    value_json=e["value_json"], is_encrypted=e["is_encrypted"],
                    created_at=now, updated_at=now,
                ))
            else:
                existing.value_json = e["value_json"]
                existing.is_encrypted = e["is_encrypted"]
                existing.updated_at = now
        await self._session.commit()
