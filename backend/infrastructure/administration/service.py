"""AdministrationService — implements IAdministrationPort.

Orchestrates: assistants, templates, workflows, rules, categories,
feature toggles, language config, users/roles, usage monitoring,
backup/restore, config export/import.
"""
from __future__ import annotations

import json
import logging
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.ports.administration import (
    IAdministrationPort, BackupConfig, SystemHealth,
)
from backend.infrastructure.administration.repository import (
    AssistantRepository, TemplateRepository, WorkflowRepository,
    RuleRepository, CategoryRepository, FeatureToggleRepository,
    LanguageConfigRepository, UsageRepository,
)

logger = logging.getLogger(__name__)


class AdministrationService(IAdministrationPort):
    """Full administration layer, all operations local."""

    def __init__(
        self,
        session_factory,          # async callable → AsyncSession
        security_service: Any,    # from Phase 6
        training_service: Any,    # from Phase 8
        inference_container: Any, # from Phase 1
        models_root: Path,
        datasets_root: Path,
        experiments_root: Path,
        checkpoints_root: Path,
        backup_root: Path,
    ) -> None:
        self._sf = session_factory
        self._security = security_service
        self._training = training_service
        self._inference = inference_container
        self._models_root = models_root
        self._datasets_root = datasets_root
        self._experiments_root = experiments_root
        self._checkpoints_root = checkpoints_root
        self._backup_root = backup_root

    # ------------------------------------------------------------------
    # IAdministrationPort
    # ------------------------------------------------------------------

    async def health_check(self) -> SystemHealth:
        components: dict[str, str] = {}
        warnings: list[str] = []

        # DB
        try:
            async with self._sf() as s:
                await s.exec(__import__("sqlmodel", fromlist=["select"]).select(__import__("sqlmodel", fromlist=["SQLModel"]).SQLModel).limit(1))
            components["db"] = "ok"
        except Exception as exc:
            components["db"] = f"error: {exc}"
            warnings.append("Database unreachable")

        # Models
        if self._inference:
            models = self._inference.loader.list_available() if hasattr(self._inference, "loader") else []
            components["models"] = f"{len(models)} loaded"
            if not models:
                warnings.append("No models available in models/")
        else:
            components["inference"] = "not initialised"
            warnings.append("Inference engine not available")

        status = "healthy" if not warnings else ("degraded" if len(warnings) < 3 else "unhealthy")
        return SystemHealth(status=status, components=components, warnings=warnings)

    async def backup(self, config: BackupConfig) -> str:
        dest = Path(config.destination_path)
        dest.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive_name = f"aegis-backup-{timestamp}"
        archive_path = self._backup_root / archive_name

        # Gather directories to include
        sources = [
            self._datasets_root,
            self._experiments_root,
            self._checkpoints_root,
        ]
        if config.include_models:
            sources.append(self._models_root)

        tmp_dir = self._backup_root / f"_tmp_{timestamp}"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        for src in sources:
            if src.exists():
                shutil.copytree(src, tmp_dir / src.name, dirs_exist_ok=True)

        shutil.make_archive(
            str(archive_path),
            "gztar" if config.compress else "tar",
            root_dir=str(tmp_dir),
        )
        shutil.rmtree(tmp_dir)
        final = str(archive_path) + (".tar.gz" if config.compress else ".tar")
        logger.info("Backup created: %s", final)
        return final

    async def restore(self, backup_path: str) -> None:
        src = Path(backup_path)
        if not src.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        shutil.unpack_archive(str(src), str(self._backup_root / "_restore_tmp"))
        logger.info("Backup unpacked from %s", backup_path)

    async def list_users(self) -> list[dict]:
        if self._security is None:
            return []
        return await self._security.list_users()

    async def create_user(self, username: str, password: str, roles: list[str]) -> dict:
        return await self._security.create_user(username, password, roles)

    async def delete_user(self, user_id: str) -> None:
        await self._security.delete_user(user_id)

    # ------------------------------------------------------------------
    # Assistants
    # ------------------------------------------------------------------

    async def create_assistant(self, **kwargs) -> dict:
        async with self._sf() as s:
            repo = AssistantRepository(s)
            obj = await repo.create(**kwargs)
            return obj.model_dump()

    async def list_assistants(self, active_only: bool = False) -> list[dict]:
        async with self._sf() as s:
            repo = AssistantRepository(s)
            items = await repo.list(active_only=active_only)
            return [i.model_dump() for i in items]

    async def get_assistant(self, id: int) -> dict | None:
        async with self._sf() as s:
            repo = AssistantRepository(s)
            obj = await repo.get(id)
            return obj.model_dump() if obj else None

    async def update_assistant(self, id: int, **kwargs) -> dict | None:
        async with self._sf() as s:
            repo = AssistantRepository(s)
            obj = await repo.update(id, **kwargs)
            return obj.model_dump() if obj else None

    async def delete_assistant(self, id: int) -> bool:
        async with self._sf() as s:
            return await AssistantRepository(s).delete(id)

    async def duplicate_assistant(self, id: int, new_name: str) -> dict | None:
        async with self._sf() as s:
            repo = AssistantRepository(s)
            obj = await repo.duplicate(id, new_name)
            return obj.model_dump() if obj else None

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    async def create_template(self, **kwargs) -> dict:
        async with self._sf() as s:
            obj = await TemplateRepository(s).create(**kwargs)
            return obj.model_dump()

    async def list_templates(self) -> list[dict]:
        async with self._sf() as s:
            items = await TemplateRepository(s).list()
            return [i.model_dump() for i in items]

    async def delete_template(self, id: int) -> bool:
        async with self._sf() as s:
            return await TemplateRepository(s).delete(id)

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    async def create_workflow(self, **kwargs) -> dict:
        async with self._sf() as s:
            obj = await WorkflowRepository(s).create(**kwargs)
            return obj.model_dump()

    async def list_workflows(self, active_only: bool = False) -> list[dict]:
        async with self._sf() as s:
            items = await WorkflowRepository(s).list(active_only=active_only)
            return [i.model_dump() for i in items]

    async def update_workflow(self, id: int, **kwargs) -> dict | None:
        async with self._sf() as s:
            obj = await WorkflowRepository(s).update(id, **kwargs)
            return obj.model_dump() if obj else None

    async def delete_workflow(self, id: int) -> bool:
        async with self._sf() as s:
            return await WorkflowRepository(s).delete(id)

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------

    async def create_rule(self, **kwargs) -> dict:
        async with self._sf() as s:
            obj = await RuleRepository(s).create(**kwargs)
            return obj.model_dump()

    async def list_rules(self, active_only: bool = False) -> list[dict]:
        async with self._sf() as s:
            items = await RuleRepository(s).list(active_only=active_only)
            return [i.model_dump() for i in items]

    async def delete_rule(self, id: int) -> bool:
        async with self._sf() as s:
            return await RuleRepository(s).delete(id)

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    async def create_category(self, **kwargs) -> dict:
        async with self._sf() as s:
            obj = await CategoryRepository(s).create(**kwargs)
            return obj.model_dump()

    async def list_categories(self) -> list[dict]:
        async with self._sf() as s:
            items = await CategoryRepository(s).list()
            return [i.model_dump() for i in items]

    async def delete_category(self, id: int) -> bool:
        async with self._sf() as s:
            return await CategoryRepository(s).delete(id)

    # ------------------------------------------------------------------
    # Feature Toggles
    # ------------------------------------------------------------------

    async def set_feature(self, key: str, enabled: bool, description: str = "") -> dict:
        async with self._sf() as s:
            obj = await FeatureToggleRepository(s).set(key, enabled, description)
            return obj.model_dump()

    async def list_features(self) -> list[dict]:
        async with self._sf() as s:
            items = await FeatureToggleRepository(s).list()
            return [i.model_dump() for i in items]

    async def is_feature_enabled(self, key: str) -> bool:
        async with self._sf() as s:
            return await FeatureToggleRepository(s).is_enabled(key)

    # ------------------------------------------------------------------
    # Language Config
    # ------------------------------------------------------------------

    async def upsert_language(self, code: str, label: str, is_enabled: bool, is_default: bool = False) -> dict:
        async with self._sf() as s:
            obj = await LanguageConfigRepository(s).upsert(code, label, is_enabled, is_default)
            return obj.model_dump()

    async def list_languages(self) -> list[dict]:
        async with self._sf() as s:
            items = await LanguageConfigRepository(s).list()
            return [i.model_dump() for i in items]

    # ------------------------------------------------------------------
    # Usage monitoring
    # ------------------------------------------------------------------

    async def record_usage(self, **kwargs) -> None:
        async with self._sf() as s:
            await UsageRepository(s).record(**kwargs)

    async def query_usage(
        self,
        event_type: str | None = None,
        user_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        async with self._sf() as s:
            items = await UsageRepository(s).query(event_type, user_id, since, limit)
            return [i.model_dump() for i in items]

    async def usage_stats(
        self,
        event_type: str | None = None,
        since: datetime | None = None,
    ) -> dict:
        async with self._sf() as s:
            return await UsageRepository(s).aggregate(event_type, since)

    # ------------------------------------------------------------------
    # Config export / import
    # ------------------------------------------------------------------

    async def export_config(self) -> dict:
        """Export full platform config as a serialisable dict."""
        assistants = await self.list_assistants()
        templates = await self.list_templates()
        workflows = await self.list_workflows()
        rules = await self.list_rules()
        categories = await self.list_categories()
        features = await self.list_features()
        languages = await self.list_languages()
        return {
            "export_version": "1",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "assistants": assistants,
            "templates": templates,
            "workflows": workflows,
            "rules": rules,
            "categories": categories,
            "feature_toggles": features,
            "languages": languages,
        }

    async def import_config(self, data: dict) -> dict:
        """Import config dict. Returns counts of imported objects."""
        counts: dict[str, int] = {}

        for tmpl in data.get("templates", []):
            tmpl.pop("id", None)
            tmpl.pop("created_at", None)
            await self.create_template(**tmpl)
        counts["templates"] = len(data.get("templates", []))

        for asst in data.get("assistants", []):
            asst.pop("id", None)
            asst.pop("created_at", None)
            asst.pop("updated_at", None)
            await self.create_assistant(**asst)
        counts["assistants"] = len(data.get("assistants", []))

        for wf in data.get("workflows", []):
            wf.pop("id", None)
            wf.pop("created_at", None)
            wf.pop("updated_at", None)
            await self.create_workflow(**wf)
        counts["workflows"] = len(data.get("workflows", []))

        for rule in data.get("rules", []):
            rule.pop("id", None)
            rule.pop("created_at", None)
            await self.create_rule(**rule)
        counts["rules"] = len(data.get("rules", []))

        for cat in data.get("categories", []):
            cat.pop("id", None)
            cat.pop("created_at", None)
            await self.create_category(**cat)
        counts["categories"] = len(data.get("categories", []))

        for ft in data.get("feature_toggles", []):
            await self.set_feature(ft["key"], ft["enabled"], ft.get("description", ""))
        counts["feature_toggles"] = len(data.get("feature_toggles", []))

        for lang in data.get("languages", []):
            await self.upsert_language(
                lang["code"], lang["label"],
                lang.get("is_enabled", True), lang.get("is_default", False)
            )
        counts["languages"] = len(data.get("languages", []))

        logger.info("Config import complete: %s", counts)
        return counts

    # ------------------------------------------------------------------
    # Model management proxy (delegates to Inference/Training)
    # ------------------------------------------------------------------

    def list_models(self) -> list[str]:
        if self._inference and hasattr(self._inference, "loader"):
            return self._inference.loader.list_available()
        return []

    def list_datasets(self) -> list[str]:
        if self._training:
            return self._training.list_datasets()
        return []

    def list_experiments(self) -> list:
        if self._training:
            return self._training.list_experiments()
        return []
