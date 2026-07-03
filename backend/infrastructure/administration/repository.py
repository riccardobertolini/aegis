"""Repository layer for Administration Engine.

All DB operations are async via aiosqlite + SQLModel.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.infrastructure.administration.models import (
    Assistant,
    AssistantTemplate,
    Category,
    FeatureToggle,
    LanguageConfig,
    Rule,
    UsageEvent,
    Workflow,
)

logger = logging.getLogger(__name__)


class AssistantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, **kwargs) -> Assistant:
        obj = Assistant(**kwargs)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get(self, id: int) -> Assistant | None:
        return await self._s.get(Assistant, id)

    async def list(self, active_only: bool = False) -> list[Assistant]:
        q = select(Assistant)
        if active_only:
            q = q.where(Assistant.is_active == True)  # noqa: E712
        result = await self._s.exec(q)
        return result.all()

    async def update(self, id: int, **kwargs) -> Assistant | None:
        obj = await self.get(id)
        if obj is None:
            return None
        for k, v in kwargs.items():
            setattr(obj, k, v)
        obj.updated_at = datetime.now(UTC)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def delete(self, id: int) -> bool:
        obj = await self.get(id)
        if obj is None:
            return False
        await self._s.delete(obj)
        await self._s.commit()
        return True

    async def duplicate(self, id: int, new_name: str) -> Assistant | None:
        original = await self.get(id)
        if original is None:
            return None
        clone = Assistant(
            name=new_name,
            description=original.description,
            model_id=original.model_id,
            system_prompt=original.system_prompt,
            template_id=original.template_id,
            meta=original.meta,
        )
        self._s.add(clone)
        await self._s.commit()
        await self._s.refresh(clone)
        return clone


class TemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, **kwargs) -> AssistantTemplate:
        obj = AssistantTemplate(**kwargs)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get(self, id: int) -> AssistantTemplate | None:
        return await self._s.get(AssistantTemplate, id)

    async def list(self) -> list[AssistantTemplate]:
        result = await self._s.exec(select(AssistantTemplate))
        return result.all()

    async def delete(self, id: int) -> bool:
        obj = await self.get(id)
        if obj is None:
            return False
        await self._s.delete(obj)
        await self._s.commit()
        return True


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, **kwargs) -> Workflow:
        obj = Workflow(**kwargs)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get(self, id: int) -> Workflow | None:
        return await self._s.get(Workflow, id)

    async def list(self, active_only: bool = False) -> list[Workflow]:
        q = select(Workflow)
        if active_only:
            q = q.where(Workflow.is_active == True)  # noqa: E712
        result = await self._s.exec(q)
        return result.all()

    async def update(self, id: int, **kwargs) -> Workflow | None:
        obj = await self.get(id)
        if obj is None:
            return None
        for k, v in kwargs.items():
            setattr(obj, k, v)
        obj.updated_at = datetime.now(UTC)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def delete(self, id: int) -> bool:
        obj = await self.get(id)
        if obj is None:
            return False
        await self._s.delete(obj)
        await self._s.commit()
        return True


class RuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, **kwargs) -> Rule:
        obj = Rule(**kwargs)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get(self, id: int) -> Rule | None:
        return await self._s.get(Rule, id)

    async def list(self, active_only: bool = False) -> list[Rule]:
        q = select(Rule).order_by(Rule.priority.desc())
        if active_only:
            q = q.where(Rule.is_active == True)  # noqa: E712
        result = await self._s.exec(q)
        return result.all()

    async def delete(self, id: int) -> bool:
        obj = await self.get(id)
        if obj is None:
            return False
        await self._s.delete(obj)
        await self._s.commit()
        return True


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, **kwargs) -> Category:
        obj = Category(**kwargs)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get(self, id: int) -> Category | None:
        return await self._s.get(Category, id)

    async def list(self) -> list[Category]:
        result = await self._s.exec(select(Category))
        return result.all()

    async def delete(self, id: int) -> bool:
        obj = await self.get(id)
        if obj is None:
            return False
        await self._s.delete(obj)
        await self._s.commit()
        return True


class FeatureToggleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def set(self, key: str, enabled: bool, description: str = "") -> FeatureToggle:
        result = await self._s.exec(select(FeatureToggle).where(FeatureToggle.key == key))
        obj = result.first()
        if obj is None:
            obj = FeatureToggle(key=key, enabled=enabled, description=description)
        else:
            obj.enabled = enabled
            obj.updated_at = datetime.now(UTC)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get(self, key: str) -> FeatureToggle | None:
        result = await self._s.exec(select(FeatureToggle).where(FeatureToggle.key == key))
        return result.first()

    async def list(self) -> list[FeatureToggle]:
        result = await self._s.exec(select(FeatureToggle))
        return result.all()

    async def is_enabled(self, key: str) -> bool:
        ft = await self.get(key)
        return ft.enabled if ft else False


class LanguageConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def upsert(self, code: str, label: str, is_enabled: bool, is_default: bool = False) -> LanguageConfig:
        result = await self._s.exec(select(LanguageConfig).where(LanguageConfig.code == code))
        obj = result.first()
        if obj is None:
            obj = LanguageConfig(code=code, label=label, is_enabled=is_enabled, is_default=is_default)
        else:
            obj.label = label
            obj.is_enabled = is_enabled
            obj.is_default = is_default
            obj.updated_at = datetime.now(UTC)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def list(self) -> list[LanguageConfig]:
        result = await self._s.exec(select(LanguageConfig))
        return result.all()

    async def get_default(self) -> LanguageConfig | None:
        result = await self._s.exec(
            select(LanguageConfig).where(LanguageConfig.is_default == True)  # noqa: E712
        )
        return result.first()


class UsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def record(self, **kwargs) -> UsageEvent:
        obj = UsageEvent(**kwargs)
        self._s.add(obj)
        await self._s.commit()
        return obj

    async def query(
        self,
        event_type: str | None = None,
        user_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[UsageEvent]:
        q = select(UsageEvent).order_by(UsageEvent.occurred_at.desc()).limit(limit)
        if event_type:
            q = q.where(UsageEvent.event_type == event_type)
        if user_id:
            q = q.where(UsageEvent.user_id == user_id)
        if since:
            q = q.where(UsageEvent.occurred_at >= since)
        result = await self._s.exec(q)
        return result.all()

    async def aggregate(
        self,
        event_type: str | None = None,
        since: datetime | None = None,
    ) -> dict:
        """Return aggregated stats: total events, total tokens, avg duration."""
        events = await self.query(event_type=event_type, since=since, limit=10_000)
        total = len(events)
        tokens = sum(e.tokens_used for e in events)
        duration = sum(e.duration_ms for e in events)
        return {
            "total_events": total,
            "total_tokens": tokens,
            "avg_duration_ms": round(duration / total, 1) if total else 0,
            "event_type": event_type or "all",
        }
