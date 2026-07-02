"""DI factory for memory engine."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.memory.service import MemoryService


@dataclass
class MemoryContainer:
    service: MemoryService


def build_memory_container(
    session: AsyncSession,
    summariser=None,
) -> MemoryContainer:
    return MemoryContainer(service=MemoryService(session=session, summariser=summariser))
