"""DI factory for the Administration Engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.infrastructure.administration.service import AdministrationService
from backend.shared.config import Settings


def build_admin_container(
    settings: Settings,
    session_factory: Any,
    security_service: Any,
    training_service: Any,
    inference_container: Any,
) -> AdministrationService:
    """Wire and return a ready AdministrationService."""
    base = Path(getattr(settings, "base_dir", "."))
    return AdministrationService(
        session_factory=session_factory,
        security_service=security_service,
        training_service=training_service,
        inference_container=inference_container,
        models_root=base / "models",
        datasets_root=base / getattr(settings, "datasets_dir", "datasets"),
        experiments_root=base / getattr(settings, "experiments_dir", "experiments"),
        checkpoints_root=base / getattr(settings, "checkpoints_dir", "checkpoints"),
        backup_root=base / getattr(settings, "backup_dir", "backups"),
    )
