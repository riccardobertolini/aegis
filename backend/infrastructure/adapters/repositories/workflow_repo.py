"""SQLite repositories for Workflow and Rule entities."""
from __future__ import annotations

from sqlmodel import select

from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository
from backend.infrastructure.database.models import RuleModel, WorkflowModel


class SQLiteWorkflowRepository(BaseSQLiteRepository[WorkflowModel]):
    model = WorkflowModel

    async def find_by_owner(self, owner_id: str) -> list[WorkflowModel]:
        result = await self._session.exec(
            select(WorkflowModel).where(WorkflowModel.owner_id == owner_id)
        )
        return list(result.all())

    async def find_by_status(self, status: str) -> list[WorkflowModel]:
        result = await self._session.exec(
            select(WorkflowModel).where(WorkflowModel.status == status)
        )
        return list(result.all())


WorkflowRepository = SQLiteWorkflowRepository


class SQLiteRuleRepository(BaseSQLiteRepository[RuleModel]):
    model = RuleModel

    async def find_active_by_resource(self, resource: str) -> list[RuleModel]:
        result = await self._session.exec(
            select(RuleModel)
            .where(RuleModel.resource == resource, RuleModel.is_active == True)  # noqa: E712
            .order_by(RuleModel.priority.desc())  # type: ignore[attr-defined]
        )
        return list(result.all())

    async def find_active(self) -> list[RuleModel]:
        result = await self._session.exec(
            select(RuleModel)
            .where(RuleModel.is_active == True)  # noqa: E712
            .order_by(RuleModel.priority.desc())  # type: ignore[attr-defined]
        )
        return list(result.all())


RuleRepository = SQLiteRuleRepository
