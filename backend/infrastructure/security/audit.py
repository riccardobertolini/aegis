"""Append-only audit log writer and reader.

Rows are chained using HMAC-SHA256:
    row_hmac = HMAC(key=audit_key, msg=prev_hmac + row_content)
This makes any tampering detectable during chain verification.

The audit_key is derived from the keystore master key; it is never stored.
"""
import hashlib
import hmac
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.domain.ports.security import AuditEntry
from backend.infrastructure.security.models import AuditLogModel

_GENESIS_HMAC = "0" * 64  # Starting value for chain


def _row_content(row: AuditLogModel) -> bytes:
    """Deterministic byte representation of auditable fields."""
    return json.dumps(
        {
            "id": row.id,
            "timestamp": row.timestamp.isoformat(),
            "event_type": row.event_type,
            "actor_id": row.actor_id,
            "resource": row.resource,
            "action": row.action,
            "outcome": row.outcome,
            "details_json": row.details_json,
        },
        sort_keys=True,
    ).encode()


class AuditWriter:
    """Appends immutable audit rows with HMAC chaining."""

    def __init__(self, session: AsyncSession, audit_key: bytes) -> None:
        self._session = session
        self._audit_key = audit_key

    async def _last_hmac(self) -> str:
        result = await self._session.execute(
            select(AuditLogModel.row_hmac)
            .order_by(AuditLogModel.timestamp.desc())
            .limit(1)
        )
        row = result.scalars().first()
        return row or _GENESIS_HMAC

    async def append(self, entry: AuditEntry) -> None:
        row = AuditLogModel(
            timestamp=entry.timestamp,
            event_type=entry.event_type,
            actor_id=entry.actor_id,
            actor_username=entry.actor_username,
            resource=entry.resource,
            action=entry.action,
            outcome=entry.outcome,
            details_json=json.dumps(entry.details),
            ip_address=entry.ip_address,
        )
        prev = await self._last_hmac()
        content = prev.encode() + _row_content(row)
        row.row_hmac = hmac.new(self._audit_key, content, hashlib.sha256).hexdigest()
        self._session.add(row)
        await self._session.commit()


class AuditReader:
    """Read and verify audit chain integrity."""

    def __init__(self, session: AsyncSession, audit_key: bytes) -> None:
        self._session = session
        self._audit_key = audit_key

    async def query(
        self,
        actor_id: str | None = None,
        resource: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        stmt = select(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).limit(limit)
        if actor_id:
            stmt = stmt.where(AuditLogModel.actor_id == actor_id)
        if resource:
            stmt = stmt.where(AuditLogModel.resource == resource)
        if since:
            stmt = stmt.where(AuditLogModel.timestamp >= since)
        if until:
            stmt = stmt.where(AuditLogModel.timestamp <= until)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [
            AuditEntry(
                event_type=r.event_type,
                actor_id=r.actor_id,
                actor_username=r.actor_username,
                resource=r.resource,
                action=r.action,
                outcome=r.outcome,
                details=json.loads(r.details_json),
                timestamp=r.timestamp,
                ip_address=r.ip_address,
            )
            for r in rows
        ]

    async def verify_chain(self) -> tuple[bool, int]:
        """Returns (is_valid, first_broken_index)."""
        result = await self._session.execute(
            select(AuditLogModel).order_by(AuditLogModel.timestamp.asc())
        )
        rows = result.scalars().all()
        prev = _GENESIS_HMAC
        for i, row in enumerate(rows):
            content = prev.encode() + _row_content(row)
            expected = hmac.new(self._audit_key, content, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, row.row_hmac or ""):
                return False, i
            prev = row.row_hmac  # type: ignore[assignment]
        return True, -1
