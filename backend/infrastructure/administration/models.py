"""SQLModel ORM models for the Administration Engine.

Covers: assistants, templates, workflows, rules, categories,
feature toggles, language config, usage metrics.

NOTE: table names here are prefixed with `admin_` to avoid collisions with
the core domain models in `backend.infrastructure.database.models`.
In particular `admin_assistants` vs `assistants` (core AssistantModel).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Assistants (admin layer — extended config, templates, etc.)
# ---------------------------------------------------------------------------

class Assistant(SQLModel, table=True):
    __tablename__ = "admin_assistants"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    model_id: str = ""
    system_prompt: str = ""
    template_id: Optional[int] = Field(default=None, foreign_key="assistant_templates.id")
    is_active: bool = True
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    meta: str = "{}"  # JSON blob for extra config


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

class AssistantTemplate(SQLModel, table=True):
    __tablename__ = "assistant_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    system_prompt: str = ""
    default_model_id: str = ""
    is_builtin: bool = False
    created_at: datetime = Field(default_factory=_now)
    meta: str = "{}"


# ---------------------------------------------------------------------------
# Workflows (admin layer)
# ---------------------------------------------------------------------------

class Workflow(SQLModel, table=True):
    __tablename__ = "admin_workflows"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    steps: str = "[]"  # JSON array of step dicts
    is_active: bool = True
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Rules (admin layer)
# ---------------------------------------------------------------------------

class Rule(SQLModel, table=True):
    __tablename__ = "admin_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    condition: str = ""   # JSON / DSL expression
    action: str = ""      # JSON action descriptor
    priority: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Categories (admin layer)
# ---------------------------------------------------------------------------

class Category(SQLModel, table=True):
    __tablename__ = "admin_categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(index=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="admin_categories.id")
    description: str = ""
    created_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Feature toggles
# ---------------------------------------------------------------------------

class FeatureToggle(SQLModel, table=True):
    __tablename__ = "feature_toggles"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    enabled: bool = False
    description: str = ""
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Language config
# ---------------------------------------------------------------------------

class LanguageConfig(SQLModel, table=True):
    __tablename__ = "language_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)   # e.g. "it", "en", "de"
    label: str = ""                               # e.g. "Italiano"
    is_enabled: bool = True
    is_default: bool = False
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Usage metrics (local monitoring)
# ---------------------------------------------------------------------------

class UsageEvent(SQLModel, table=True):
    __tablename__ = "usage_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str = Field(index=True)  # "inference", "training", "document", etc.
    user_id: Optional[str] = Field(default=None, index=True)
    model_id: Optional[str] = None
    tokens_used: int = 0
    duration_ms: int = 0
    status: str = "ok"  # "ok" | "error"
    occurred_at: datetime = Field(default_factory=_now, index=True)
    meta: str = "{}"
