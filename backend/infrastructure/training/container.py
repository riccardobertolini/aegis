"""DI factory for the Training Engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.shared.config import Settings
from backend.infrastructure.training.dataset import DatasetManager
from backend.infrastructure.training.experiment import ExperimentTracker
from backend.infrastructure.training.checkpoint import CheckpointManager
from backend.infrastructure.training.signer import ModelSigner
from backend.infrastructure.training.service import TrainingService


def build_training_container(
    settings: Settings,
    model_loader: Any,
) -> TrainingService:
    """Wire all training components and return a ready TrainingService.

    Parameters
    ----------
    settings:
        App settings (provides base paths).
    model_loader:
        ``MambaModelLoader`` instance from the Inference container (Phase 1).
    """
    models_root = Path(settings.models_dir)  # e.g. "models"
    datasets_root = Path(getattr(settings, "datasets_dir", "datasets"))
    experiments_root = Path(getattr(settings, "experiments_dir", "experiments"))
    checkpoints_root = Path(getattr(settings, "checkpoints_dir", "checkpoints"))

    hmac_secret_str: str = getattr(settings, "model_hmac_secret", "aegis-training-secret")
    hmac_secret = hmac_secret_str.encode()

    dataset_manager = DatasetManager(datasets_root)
    tracker = ExperimentTracker(experiments_root)
    checkpoint_manager = CheckpointManager(checkpoints_root)
    signer = ModelSigner(hmac_secret=hmac_secret)

    return TrainingService(
        model_loader=model_loader,
        dataset_manager=dataset_manager,
        tracker=tracker,
        checkpoint_manager=checkpoint_manager,
        signer=signer,
        models_root=models_root,
    )
