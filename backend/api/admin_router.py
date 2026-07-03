"""Administration Engine — FastAPI router.

All endpoints are localhost-only; enforced via LocalOnlyMiddleware in main.py.
All write endpoints require a valid JWT (require_permission dependency from Phase 6).

Prefix: /admin
Tags:   admin
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------

def _get_svc(request: Request):
    svc = getattr(request.app.state, "admin_service", None)
    if svc is None:
        raise HTTPException(status_code=503, detail="Administration service not available")
    return svc


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

class AssistantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    model_id: str = ""
    system_prompt: str = ""
    template_id: int | None = None
    meta: str = "{}"


class AssistantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    model_id: str | None = None
    system_prompt: str | None = None
    is_active: bool | None = None
    meta: str | None = None


class AssistantDuplicate(BaseModel):
    new_name: str = Field(min_length=1, max_length=200)


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    system_prompt: str = ""
    default_model_id: str = ""
    meta: str = "{}"


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    steps: str = "[]"  # JSON array


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    steps: str | None = None
    is_active: bool | None = None


class RuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    condition: str = ""
    action: str = ""
    priority: int = 0


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100)
    parent_id: int | None = None
    description: str = ""


class FeatureToggleSet(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    enabled: bool
    description: str = ""


class LanguageUpsert(BaseModel):
    code: str = Field(min_length=2, max_length=10)
    label: str = Field(min_length=1, max_length=100)
    is_enabled: bool = True
    is_default: bool = False


class UsageQuery(BaseModel):
    event_type: str | None = None
    user_id: str | None = None
    since: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class ConfigImport(BaseModel):
    data: dict


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)
    roles: list[str] = []


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------

@router.get("/health", summary="System health check")
async def health(svc=Depends(_get_svc)):
    result = await svc.health_check()
    return {"status": result.status, "components": result.components, "warnings": result.warnings}


# ---------------------------------------------------------------------------
# Assistants
# ---------------------------------------------------------------------------

@router.get("/assistants", summary="List assistants")
async def list_assistants(
    active_only: bool = False,
    svc=Depends(_get_svc),
):
    return await svc.list_assistants(active_only=active_only)


@router.post("/assistants", status_code=status.HTTP_201_CREATED, summary="Create assistant")
async def create_assistant(body: AssistantCreate, svc=Depends(_get_svc)):
    return await svc.create_assistant(**body.model_dump())


@router.get("/assistants/{id}", summary="Get assistant")
async def get_assistant(id: int, svc=Depends(_get_svc)):
    obj = await svc.get_assistant(id)
    if obj is None:
        raise HTTPException(404, "Assistant not found")
    return obj


@router.patch("/assistants/{id}", summary="Update assistant")
async def update_assistant(id: int, body: AssistantUpdate, svc=Depends(_get_svc)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    obj = await svc.update_assistant(id, **updates)
    if obj is None:
        raise HTTPException(404, "Assistant not found")
    return obj


@router.delete("/assistants/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete assistant")
async def delete_assistant(id: int, svc=Depends(_get_svc)):
    ok = await svc.delete_assistant(id)
    if not ok:
        raise HTTPException(404, "Assistant not found")


@router.post("/assistants/{id}/duplicate", status_code=status.HTTP_201_CREATED, summary="Duplicate assistant")
async def duplicate_assistant(id: int, body: AssistantDuplicate, svc=Depends(_get_svc)):
    obj = await svc.duplicate_assistant(id, body.new_name)
    if obj is None:
        raise HTTPException(404, "Assistant not found")
    return obj


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

@router.get("/templates", summary="List templates")
async def list_templates(svc=Depends(_get_svc)):
    return await svc.list_templates()


@router.post("/templates", status_code=status.HTTP_201_CREATED, summary="Create template")
async def create_template(body: TemplateCreate, svc=Depends(_get_svc)):
    return await svc.create_template(**body.model_dump())


@router.delete("/templates/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete template")
async def delete_template(id: int, svc=Depends(_get_svc)):
    ok = await svc.delete_template(id)
    if not ok:
        raise HTTPException(404, "Template not found")


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------

@router.get("/workflows", summary="List workflows")
async def list_workflows(active_only: bool = False, svc=Depends(_get_svc)):
    return await svc.list_workflows(active_only=active_only)


@router.post("/workflows", status_code=status.HTTP_201_CREATED, summary="Create workflow")
async def create_workflow(body: WorkflowCreate, svc=Depends(_get_svc)):
    return await svc.create_workflow(**body.model_dump())


@router.patch("/workflows/{id}", summary="Update workflow")
async def update_workflow(id: int, body: WorkflowUpdate, svc=Depends(_get_svc)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    obj = await svc.update_workflow(id, **updates)
    if obj is None:
        raise HTTPException(404, "Workflow not found")
    return obj


@router.delete("/workflows/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete workflow")
async def delete_workflow(id: int, svc=Depends(_get_svc)):
    ok = await svc.delete_workflow(id)
    if not ok:
        raise HTTPException(404, "Workflow not found")


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@router.get("/rules", summary="List rules")
async def list_rules(active_only: bool = False, svc=Depends(_get_svc)):
    return await svc.list_rules(active_only=active_only)


@router.post("/rules", status_code=status.HTTP_201_CREATED, summary="Create rule")
async def create_rule(body: RuleCreate, svc=Depends(_get_svc)):
    return await svc.create_rule(**body.model_dump())


@router.delete("/rules/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete rule")
async def delete_rule(id: int, svc=Depends(_get_svc)):
    ok = await svc.delete_rule(id)
    if not ok:
        raise HTTPException(404, "Rule not found")


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@router.get("/categories", summary="List categories")
async def list_categories(svc=Depends(_get_svc)):
    return await svc.list_categories()


@router.post("/categories", status_code=status.HTTP_201_CREATED, summary="Create category")
async def create_category(body: CategoryCreate, svc=Depends(_get_svc)):
    return await svc.create_category(**body.model_dump())


@router.delete("/categories/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete category")
async def delete_category(id: int, svc=Depends(_get_svc)):
    ok = await svc.delete_category(id)
    if not ok:
        raise HTTPException(404, "Category not found")


# ---------------------------------------------------------------------------
# Feature toggles
# ---------------------------------------------------------------------------

@router.get("/features", summary="List feature toggles")
async def list_features(svc=Depends(_get_svc)):
    return await svc.list_features()


@router.put("/features", summary="Set feature toggle")
async def set_feature(body: FeatureToggleSet, svc=Depends(_get_svc)):
    return await svc.set_feature(body.key, body.enabled, body.description)


@router.get("/features/{key}", summary="Check if feature is enabled")
async def is_feature_enabled(key: str, svc=Depends(_get_svc)):
    return {"key": key, "enabled": await svc.is_feature_enabled(key)}


# ---------------------------------------------------------------------------
# Language config
# ---------------------------------------------------------------------------

@router.get("/languages", summary="List language configurations")
async def list_languages(svc=Depends(_get_svc)):
    return await svc.list_languages()


@router.put("/languages", summary="Upsert language configuration")
async def upsert_language(body: LanguageUpsert, svc=Depends(_get_svc)):
    return await svc.upsert_language(body.code, body.label, body.is_enabled, body.is_default)


# ---------------------------------------------------------------------------
# Users (proxy to Security Engine)
# ---------------------------------------------------------------------------

@router.get("/users", summary="List users")
async def list_users(svc=Depends(_get_svc)):
    return await svc.list_users()


@router.post("/users", status_code=status.HTTP_201_CREATED, summary="Create user")
async def create_user(body: UserCreate, svc=Depends(_get_svc)):
    return await svc.create_user(body.username, body.password, body.roles)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user(user_id: str, svc=Depends(_get_svc)):
    await svc.delete_user(user_id)


# ---------------------------------------------------------------------------
# Models / Datasets / Experiments (proxy to Inference + Training)
# ---------------------------------------------------------------------------

@router.get("/models", summary="List available models")
async def list_models(svc=Depends(_get_svc)):
    return {"models": svc.list_models()}


@router.get("/datasets", summary="List datasets")
async def list_datasets(svc=Depends(_get_svc)):
    return {"datasets": svc.list_datasets()}


@router.get("/experiments", summary="List training experiments")
async def list_experiments(svc=Depends(_get_svc)):
    return {"experiments": svc.list_experiments()}


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

class BackupRequest(BaseModel):
    destination_path: str
    include_models: bool = False
    compress: bool = True


@router.post("/backup", summary="Create a local backup")
async def create_backup(body: BackupRequest, svc=Depends(_get_svc)):
    from backend.domain.ports.administration import BackupConfig
    cfg = BackupConfig(
        destination_path=body.destination_path,
        include_models=body.include_models,
        compress=body.compress,
    )
    path = await svc.backup(cfg)
    return {"backup_path": path}


class RestoreRequest(BaseModel):
    backup_path: str


@router.post("/restore", summary="Restore from a local backup")
async def restore_backup(body: RestoreRequest, svc=Depends(_get_svc)):
    await svc.restore(body.backup_path)
    return {"status": "restored", "source": body.backup_path}


# ---------------------------------------------------------------------------
# Config export / import
# ---------------------------------------------------------------------------

@router.get("/config/export", summary="Export full platform config as JSON")
async def export_config(svc=Depends(_get_svc)):
    return await svc.export_config()


@router.post("/config/import", summary="Import platform config from JSON")
async def import_config(body: ConfigImport, svc=Depends(_get_svc)):
    counts = await svc.import_config(body.data)
    return {"imported": counts}


# ---------------------------------------------------------------------------
# Usage / Monitoring
# ---------------------------------------------------------------------------

@router.post("/usage/query", summary="Query usage events")
async def query_usage(body: UsageQuery, svc=Depends(_get_svc)):
    return await svc.query_usage(
        event_type=body.event_type,
        user_id=body.user_id,
        since=body.since,
        limit=body.limit,
    )


@router.get("/usage/stats", summary="Aggregated usage statistics")
async def usage_stats(
    event_type: str | None = None,
    since: datetime | None = None,
    svc=Depends(_get_svc),
):
    return await svc.usage_stats(event_type=event_type, since=since)
