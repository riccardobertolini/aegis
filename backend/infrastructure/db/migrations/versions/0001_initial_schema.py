"""0001 — Initial schema: all core Aegis tables.

Revision ID: 0001
Revises: —
Create Date: 2026-07-02
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------ roles
    op.create_table(
        "role",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --------------------------------------------------------------- permissions
    op.create_table(
        "permission",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("role_id", sa.String, sa.ForeignKey("role.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource", sa.String(128), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_permission_role_id", "permission", ["role_id"])

    # ------------------------------------------------------------------ users
    op.create_table(
        "user",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("username", sa.String(128), nullable=False, unique=True),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("hashed_password", sa.Text, nullable=False),
        sa.Column("role_id", sa.String, sa.ForeignKey("role.id"), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("last_login", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_user_username", "user", ["username"])

    # --------------------------------------------------------------- assistants
    op.create_table(
        "assistant",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("system_prompt_enc", sa.Text, nullable=True),
        sa.Column("config_enc", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("owner_id", sa.String, sa.ForeignKey("user.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --------------------------------------------------------- knowledge bases
    op.create_table(
        "knowledgebase",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String(256), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("assistant_id", sa.String, sa.ForeignKey("assistant.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ---------------------------------------------------------------- categories
    op.create_table(
        "category",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("knowledge_base_id", sa.String, sa.ForeignKey("knowledgebase.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.String, sa.ForeignKey("category.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # --------------------------------------------------------------- documents
    op.create_table(
        "document",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("is_encrypted", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("knowledge_base_id", sa.String, sa.ForeignKey("knowledgebase.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_id", sa.String, sa.ForeignKey("category.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uploader_id", sa.String, sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_document_sha256", "document", ["sha256"])
    op.create_index("ix_document_knowledge_base_id", "document", ["knowledge_base_id"])

    # ----------------------------------------------------------------- models
    op.create_table(
        "aegismodel",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("architecture", sa.String(64), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ---------------------------------------------------------------- datasets
    op.create_table(
        "dataset",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("model_id", sa.String, sa.ForeignKey("aegismodel.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="'pending'"),
        sa.Column("row_count", sa.Integer, nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ----------------------------------------------------------------- memory
    op.create_table(
        "memorychunk",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("assistant_id", sa.String, sa.ForeignKey("assistant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=True),
        sa.Column("content_enc", sa.Text, nullable=False),
        sa.Column("embedding_path", sa.String(1024), nullable=True),
        sa.Column("importance", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_memorychunk_assistant_id", "memorychunk", ["assistant_id"])

    # --------------------------------------------------------------- versions
    op.create_table(
        "version",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String, nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("tag", sa.String(64), nullable=True),
        sa.Column("snapshot_json", sa.Text, nullable=False),
        sa.Column("created_by", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_version_entity", "version", ["entity_type", "entity_id"])

    # --------------------------------------------------------------- workflows
    op.create_table(
        "workflow",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("definition_json", sa.Text, nullable=False),
        sa.Column("assistant_id", sa.String, sa.ForeignKey("assistant.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ---------------------------------------------------------------- backups
    op.create_table(
        "backuprecord",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("is_encrypted", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("backup_type", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # ------------------------------------------------------------- audit log
    op.create_table(
        "auditlogentry",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("actor_id", sa.String, nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("resource", sa.String(256), nullable=True),
        sa.Column("resource_id", sa.String, nullable=True),
        sa.Column("detail_json", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_auditlogentry_actor_id", "auditlogentry", ["actor_id"])
    op.create_index("ix_auditlogentry_action", "auditlogentry", ["action"])
    op.create_index("ix_auditlogentry_created_at", "auditlogentry", ["created_at"])


def downgrade() -> None:
    for table in [
        "auditlogentry",
        "backuprecord",
        "workflow",
        "version",
        "memorychunk",
        "dataset",
        "aegismodel",
        "document",
        "category",
        "knowledgebase",
        "assistant",
        "user",
        "permission",
        "role",
    ]:
        op.drop_table(table)
