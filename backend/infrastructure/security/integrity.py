"""Model file integrity: SHA-256 hashing and verification."""
import hashlib
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.domain.ports.security import ModelIntegrityResult
from backend.infrastructure.security.models import ModelHashModel


_CHUNK = 1 << 20  # 1 MiB read chunks


def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


class ModelIntegrityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(self, model_id: str, model_path: str) -> str:
        """Hash the model file and store the fingerprint."""
        hash_value = _hash_file(model_path)
        existing = await self._session.get(ModelHashModel, model_id)
        if existing:
            existing.hash_value = hash_value
            existing.registered_at = datetime.utcnow()
            self._session.add(existing)
        else:
            self._session.add(ModelHashModel(
                model_id=model_id,
                algorithm="sha256",
                hash_value=hash_value,
            ))
        await self._session.commit()
        return hash_value

    async def verify(self, model_id: str, model_path: str) -> ModelIntegrityResult:
        """Compare stored hash against current file hash."""
        result = await self._session.execute(
            select(ModelHashModel).where(ModelHashModel.model_id == model_id)
        )
        record = result.scalars().first()
        stored = record.hash_value if record else ""
        computed = _hash_file(model_path)
        is_valid = stored == computed
        if record:
            record.last_verified_at = datetime.utcnow()
            record.last_verified_ok = is_valid
            self._session.add(record)
            await self._session.commit()
        return ModelIntegrityResult(
            model_id=model_id,
            is_valid=is_valid,
            stored_hash=stored,
            computed_hash=computed,
        )
