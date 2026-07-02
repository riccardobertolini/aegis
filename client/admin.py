"""Administration API client methods."""
from __future__ import annotations

from .base import AegisClient


class AdminMixin(AegisClient):
    """Methods for /admin endpoints."""

    BASE = "/admin"

    def health(self) -> dict:  # type: ignore[override]
        """GET /admin/health"""
        return self._get(f"{self.BASE}/health")

    # ── Assistants ────────────────────────────────────────────────────────────

    def list_assistants(self, active_only: bool = False) -> list[dict]:
        return self._get(f"{self.BASE}/assistants", active_only=active_only)

    def create_assistant(self, name: str, **kwargs) -> dict:
        return self._post(f"{self.BASE}/assistants", json={"name": name, **kwargs})

    def get_assistant(self, id: int) -> dict:
        return self._get(f"{self.BASE}/assistants/{id}")

    def update_assistant(self, id: int, **updates) -> dict:
        return self._post(f"{self.BASE}/assistants/{id}", json=updates)  # PATCH semantics

    def delete_assistant(self, id: int) -> None:
        self._delete(f"{self.BASE}/assistants/{id}")

    def duplicate_assistant(self, id: int, new_name: str) -> dict:
        return self._post(f"{self.BASE}/assistants/{id}/duplicate", json={"new_name": new_name})

    # ── Templates ─────────────────────────────────────────────────────────────

    def list_templates(self) -> list[dict]:
        return self._get(f"{self.BASE}/templates")

    def create_template(self, name: str, **kwargs) -> dict:
        return self._post(f"{self.BASE}/templates", json={"name": name, **kwargs})

    def delete_template(self, id: int) -> None:
        self._delete(f"{self.BASE}/templates/{id}")

    # ── Features ──────────────────────────────────────────────────────────────

    def list_features(self) -> list[dict]:
        return self._get(f"{self.BASE}/features")

    def set_feature(self, key: str, enabled: bool, description: str = "") -> dict:
        return self._post(f"{self.BASE}/features", json={"key": key, "enabled": enabled, "description": description})

    # ── Models / Datasets / Experiments ───────────────────────────────────────

    def list_models(self) -> dict:
        return self._get(f"{self.BASE}/models")

    def list_datasets(self) -> dict:
        return self._get(f"{self.BASE}/datasets")

    def list_experiments(self) -> dict:
        return self._get(f"{self.BASE}/experiments")

    # ── Config ────────────────────────────────────────────────────────────────

    def export_config(self) -> dict:
        return self._get(f"{self.BASE}/config/export")

    def import_config(self, data: dict) -> dict:
        return self._post(f"{self.BASE}/config/import", json={"data": data})

    # ── Backup ────────────────────────────────────────────────────────────────

    def create_backup(self, destination_path: str, include_models: bool = False, compress: bool = True) -> dict:
        return self._post(
            f"{self.BASE}/backup",
            json={"destination_path": destination_path, "include_models": include_models, "compress": compress},
        )

    def restore_backup(self, backup_path: str) -> dict:
        return self._post(f"{self.BASE}/restore", json={"backup_path": backup_path})
