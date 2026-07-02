"""Concrete SQLite Workflow and Rule repositories."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.workflow import Rule, Workflow, WorkflowStatus
from backend.domain.ports.repository import IRuleRepository, IWorkflowRepository
from backend.infrastructure.database.mappers import orm_to_rule, orm_to_workflow, rule_to_orm, workflow_to_orm
from backend.infrastructure.database.models import RuleModel, WorkflowModel
from .base_sqlite import BaseSQLiteRepository


class SQLiteWorkflowRepository(BaseSQLiteRepository[Workflow, WorkflowModel], IWorkflowRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WorkflowModel, workflow_to_orm, orm_to_workflow)

    async def list_by_owner(self, owner_id: str) -> list[Workflow]:
        stmt = select(WorkflowModel).where(WorkflowModel.owner_id == owner_id)
        result = await self._session.execute(stmt)
        return [orm_to_workflow(m) for m in result.scalars().all()]

    async def list_active(self) -> list[Workflow]:
        stmt = select(WorkflowModel).where(WorkflowModel.status == WorkflowStatus.ACTIVE.value)
        result = await self._session.execute(stmt)
        return [orm_to_workflow(m) for m in result.scalars().all()]


class SQLiteRuleRepository(BaseSQLiteRepository[Rule, RuleModel], IRuleRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RuleModel, rule_to_orm, orm_to_rule)

    async def list_by_resource(self, resource: str) -> list[Rule]:
        stmt = select(RuleModel).where(RuleModel.resource == resource)
        result = await self._session.execute(stmt)
        return [orm_to_rule(m) for m in result.scalars().all()]

    async def list_active_ordered(self) -> list[Rule]:
        stmt = (
            select(RuleModel)
            .where(RuleModel.is_active == True)  # noqa: E712
            .order_by(RuleModel.priority.desc())
        )
        result = await self._session.execute(stmt)
        return [orm_to_rule(m) for m in result.scalars().all()]
