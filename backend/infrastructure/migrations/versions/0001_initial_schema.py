"""0001 — initial schema: all FASE 2 tables.

Revision ID: 0001_initial
Revises: 
Create Date: 2026-07-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("description", sa.String, default=""),
        sa.Column("resource", sa.String, default=""),
        sa.Column("action", sa.String, default=""),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_permissions_resource", "permissions", ["resource"])

    op.create_table(
        "roles",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("description", sa.String, default=""),
        sa.Column("permissions_json", sa.Text, default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("username", sa.String, nullable=False, unique=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("hashed_password", sa.String, default=""),
        sa.Column("role_ids_json", sa.Text, default="[]"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_superadmin", sa.Boolean, default=False),
        sa.Column("last_login_at", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "assistants",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, default=""),
        sa.Column("owner_id", sa.String, nullable=False),
        sa.Column("config_json", sa.Text, default="{}"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("version", sa.Integer, default=1),
        sa.Column("knowledge_base_ids_json", sa.Text, default="[]"),
        sa.Column("plugin_ids_json", sa.Text, default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_assistants_owner_id", "assistants", ["owner_id"])

    op.create_table(
        "categories",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, default=""),
        sa.Column("parent_id", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("filename", sa.String, default=""),
        sa.Column("original_filename", sa.String, default=""),
        sa.Column("mime_type", sa.String, default=""),
        sa.Column("size_bytes", sa.Integer, default=0),
        sa.Column("checksum_sha256", sa.String, default=""),
        sa.Column("storage_path", sa.String, default=""),
        sa.Column("status", sa.String, default="pending"),
        sa.Column("owner_id", sa.String, nullable=False),
        sa.Column("category_ids_json", sa.Text, default="[]"),
        sa.Column("knowledge_base_ids_json", sa.Text, default="[]"),
        sa.Column("metadata_json", sa.Text, default="{}"),
        sa.Column("is_encrypted", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_documents_checksum", "documents", ["checksum_sha256"])
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"])
    op.create_index("ix_documents_status", "documents", ["status"])

    op.create_table(
        "knowledge_bases",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("description", sa.String, default=""),
        sa.Column("owner_id", sa.String, nullable=False),
        sa.Column("category_ids_json", sa.Text, default="[]"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("chroma_collection_name", sa.String, default=""),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "memory_entries",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("session_id", sa.String, nullable=False),
        sa.Column("assistant_id", sa.String, nullable=False),
        sa.Column("user_id", sa.String, nullable=False),
        sa.Column("role", sa.String, default="user"),
        sa.Column("content", sa.Text, default=""),
        sa.Column("embedding_id", sa.String, nullable=True),
        sa.Column("metadata_json", sa.Text, default="{}"),
        sa.Column("is_encrypted", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_memory_session_id", "memory_entries", ["session_id"])
    op.create_index("ix_memory_assistant_id", "memory_entries", ["assistant_id"])

    op.create_table(
        "model_records",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("model_type", sa.String, default="ssm_mamba"),
        sa.Column("status", sa.String, default="unavailable"),
        sa.Column("storage_path", sa.String, default=""),
        sa.Column("checksum_sha256", sa.String, default=""),
        sa.Column("size_bytes", sa.Integer, default=0),
        sa.Column("architecture", sa.String, default=""),
        sa.Column("context_length", sa.Integer, default=2048),
        sa.Column("metadata_json", sa.Text, default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_model_records_status", "model_records", ["status"])

    op.create_table(
        "datasets",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, default=""),
        sa.Column("storage_path", sa.String, default=""),
        sa.Column("format", sa.String, default="jsonl"),
        sa.Column("size_bytes", sa.Integer, default=0),
        sa.Column("checksum_sha256", sa.String, default=""),
        sa.Column("row_count", sa.Integer, default=0),
        sa.Column("owner_id", sa.String, nullable=False),
        sa.Column("metadata_json", sa.Text, default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "workflows",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, default=""),
        sa.Column("owner_id", sa.String, nullable=False),
        sa.Column("status", sa.String, default="draft"),
        sa.Column("steps_json", sa.Text, default="[]"),
        sa.Column("metadata_json", sa.Text, default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "rules",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, default=""),
        sa.Column("resource", sa.String, nullable=False),
        sa.Column("condition_json", sa.Text, default="{}"),
        sa.Column("action", sa.String, default=""),
        sa.Column("priority", sa.Integer, default=0),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("owner_id", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_rules_resource", "rules", ["resource"])
    op.create_index("ix_rules_is_active", "rules", ["is_active"])
    op.create_index("ix_rules_priority", "rules", ["priority"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("actor_id", sa.String, nullable=False),
        sa.Column("actor_username", sa.String, default=""),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("resource_type", sa.String, nullable=False),
        sa.Column("resource_id", sa.String, nullable=False),
        sa.Column("outcome", sa.String, default="ok"),
        sa.Column("ip_address", sa.String, nullable=True),
        sa.Column("details_json", sa.Text, default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_audit_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_action", "audit_logs", ["action"])
    op.create_index("ix_audit_resource", "audit_logs", ["resource_type", "resource_id"])

    op.create_table(
        "backups",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("label", sa.String, default=""),
        sa.Column("storage_path", sa.String, default=""),
        sa.Column("checksum_sha256", sa.String, default=""),
        sa.Column("size_bytes", sa.Integer, default=0),
        sa.Column("status", sa.String, default="pending"),
        sa.Column("includes_json", sa.Text, default="[]"),
        sa.Column("initiated_by", sa.String, default=""),
        sa.Column("error_message", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_backups_status", "backups", ["status"])

    op.create_table(
        "config_entries",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("scope", sa.String, nullable=False),
        sa.Column("key", sa.String, nullable=False),
        sa.Column("value_json", sa.Text, default="null"),
        sa.Column("is_encrypted", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_config_scope_key", "config_entries", ["scope", "key"], unique=True)


def downgrade() -> None:
    for table in [
        "config_entries", "backups", "audit_logs", "rules",
        "workflows", "datasets", "model_records", "memory_entries",
        "knowledge_bases", "documents", "categories", "assistants",
        "users", "roles", "permissions",
    ]:
        op.drop_table(table)
