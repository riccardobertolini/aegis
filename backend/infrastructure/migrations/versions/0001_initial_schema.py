"""Initial schema — all Aegis tables.

Revision ID: 0001
Revises: —
Create Date: 2026-07-02

Creates all 16 domain tables in a single migration.
Uses render_as_batch=True (set in env.py) for SQLite compatibility.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("resource", sa.String(), nullable=False, server_default=""),
        sa.Column("action", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_permissions_name", "permissions", ["name"])
    op.create_index("ix_permissions_resource", "permissions", ["resource"])

    op.create_table(
        "roles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("permissions_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=False, server_default=""),
        sa.Column("role_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("last_login_at", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "assistants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("config_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("knowledge_base_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("plugin_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assistants_name", "assistants", ["name"])
    op.create_index("ix_assistants_owner_id", "assistants", ["owner_id"])

    op.create_table(
        "categories",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("parent_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("filename", sa.String(), nullable=False, server_default=""),
        sa.Column("original_filename", sa.String(), nullable=False, server_default=""),
        sa.Column("mime_type", sa.String(), nullable=False, server_default=""),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checksum_sha256", sa.String(), nullable=False, server_default=""),
        sa.Column("storage_path", sa.String(), nullable=False, server_default=""),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("category_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("knowledge_base_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_checksum_sha256", "documents", ["checksum_sha256"])

    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("category_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("chroma_collection_name", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_bases_owner_id", "knowledge_bases", ["owner_id"])

    op.create_table(
        "memory_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("assistant_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("content", sa.String(), nullable=False, server_default=""),
        sa.Column("embedding_id", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_memory_entries_session_id", "memory_entries", ["session_id"])
    op.create_index("ix_memory_entries_assistant_id", "memory_entries", ["assistant_id"])
    op.create_index("ix_memory_entries_user_id", "memory_entries", ["user_id"])

    op.create_table(
        "model_records",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("model_type", sa.String(), nullable=False, server_default="ssm_mamba"),
        sa.Column("status", sa.String(), nullable=False, server_default="unavailable"),
        sa.Column("storage_path", sa.String(), nullable=False, server_default=""),
        sa.Column("checksum_sha256", sa.String(), nullable=False, server_default=""),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("architecture", sa.String(), nullable=False, server_default=""),
        sa.Column("context_length", sa.Integer(), nullable=False, server_default="2048"),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_model_records_status", "model_records", ["status"])

    op.create_table(
        "datasets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("storage_path", sa.String(), nullable=False, server_default=""),
        sa.Column("format", sa.String(), nullable=False, server_default="jsonl"),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checksum_sha256", sa.String(), nullable=False, server_default=""),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_datasets_owner_id", "datasets", ["owner_id"])

    op.create_table(
        "workflows",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("steps_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workflows_owner_id", "workflows", ["owner_id"])
    op.create_index("ix_workflows_status", "workflows", ["status"])

    op.create_table(
        "rules",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("resource", sa.String(), nullable=False),
        sa.Column("condition_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("action", sa.String(), nullable=False, server_default=""),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rules_resource", "rules", ["resource"])
    op.create_index("ix_rules_is_active", "rules", ["is_active"])
    op.create_index("ix_rules_priority", "rules", ["priority"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("actor_username", sa.String(), nullable=False, server_default=""),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("resource_id", sa.String(), nullable=False),
        sa.Column("outcome", sa.String(), nullable=False, server_default="ok"),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("details_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])

    op.create_table(
        "backups",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("label", sa.String(), nullable=False, server_default=""),
        sa.Column("storage_path", sa.String(), nullable=False, server_default=""),
        sa.Column("checksum_sha256", sa.String(), nullable=False, server_default=""),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("includes_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("initiated_by", sa.String(), nullable=False, server_default=""),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_backups_status", "backups", ["status"])

    op.create_table(
        "config_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value_json", sa.String(), nullable=False, server_default="null"),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_config_entries_scope", "config_entries", ["scope"])
    op.create_index("ix_config_entries_key", "config_entries", ["key"])


def downgrade() -> None:
    op.drop_table("config_entries")
    op.drop_table("backups")
    op.drop_table("audit_logs")
    op.drop_table("rules")
    op.drop_table("workflows")
    op.drop_table("datasets")
    op.drop_table("model_records")
    op.drop_table("memory_entries")
    op.drop_table("knowledge_bases")
    op.drop_table("documents")
    op.drop_table("categories")
    op.drop_table("assistants")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("permissions")
