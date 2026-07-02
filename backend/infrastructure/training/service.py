"""TrainingService — implements ITrainingPort, orchestrates all sub-components."""
from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

from backend.domain.ports.training import (
    ITrainingPort, JobStatus, TrainingConfig, TrainingJob,
)
from backend.infrastructure.training.dataset import DatasetManager
from backend.infrastructure.training.preprocessor import Preprocessor
from backend.infrastructure.training.experiment import ExperimentTracker
from backend.infrastructure.training.checkpoint import CheckpointManager
from backend.infrastructure.training.trainer import LocalTrainer
from backend.infrastructure.training.signer import ModelSigner
from backend.infrastructure.training.evaluator import Evaluator

logger = logging.getLogger(__name__)


class TrainingService(ITrainingPort):
    """Coordinates dataset loading, training, evaluation and model promotion."""

    def __init__(
        self,
        model_loader: Any,
        dataset_manager: DatasetManager,
        tracker: ExperimentTracker,
        checkpoint_manager: CheckpointManager,
        signer: ModelSigner,
        models_root: Path,
    ) -> None:
        self._loader = model_loader
        self._datasets = dataset_manager
        self._tracker = tracker
        self._ckpt = checkpoint_manager
        self._signer = signer
        self._models_root = models_root

        self._jobs: dict[str, TrainingJob] = {}
        self._tasks: dict[str, asyncio.Task] = {}

        self._trainer = LocalTrainer(
            model_loader=model_loader,
            checkpoint_manager=checkpoint_manager,
            tracker=tracker,
            models_root=models_root,
            on_progress=self._on_progress,
        )

    # ------------------------------------------------------------------
    # ITrainingPort
    # ------------------------------------------------------------------

    async def start_job(self, config: TrainingConfig) -> TrainingJob:
        job = TrainingJob(config=config, status=JobStatus.PENDING)
        self._jobs[config.job_id] = job

        task = asyncio.create_task(self._run_job(job))
        self._tasks[config.job_id] = task
        logger.info("Training job '%s' queued", config.job_id)
        return job

    async def get_job(self, job_id: str) -> TrainingJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")
        return job

    async def cancel_job(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            self._trainer.cancel(job_id)
            task = self._tasks.get(job_id)
            if task:
                task.cancel()
            job.status = JobStatus.CANCELLED
            logger.info("Job '%s' cancelled", job_id)

    async def list_jobs(self) -> list[TrainingJob]:
        return list(self._jobs.values())

    # ------------------------------------------------------------------
    # Extra API (exposed via router)
    # ------------------------------------------------------------------

    def list_datasets(self) -> list[str]:
        return self._datasets.list_datasets()

    def list_experiments(self):
        return self._tracker.list_runs()

    def get_experiment_metrics(self, run_id: str):
        return self._tracker.get_metrics(run_id)

    def list_checkpoints(self, run_id: str):
        return self._ckpt.list_checkpoints(run_id)

    def verify_model(self, model_id: str) -> bool:
        model_dir = self._models_root / model_id
        return self._signer.verify(model_dir)

    def sign_model(self, model_id: str) -> dict:
        model_dir = self._models_root / model_id
        return self._signer.sign(model_dir)

    def evaluate_model(self, model_id: str, dataset_name: str, max_chunks: int = 64) -> dict:
        version = self._datasets.get_latest_version(dataset_name, split="eval")
        if version is None:
            raise ValueError(f"No eval split found for dataset '{dataset_name}'")
        tokenizer = self._loader.get_tokenizer(model_id)
        if tokenizer is None:
            self._loader.load(model_id)
            tokenizer = self._loader.get_tokenizer(model_id)
        preprocessor = Preprocessor(tokenizer)
        chunks = preprocessor.process_samples(self._datasets.iter_samples(version))
        chunks = chunks[:max_chunks]
        model = self._loader.get_model(model_id) or self._loader.load(model_id)
        evaluator = Evaluator(model)
        result = evaluator.evaluate(chunks)
        return {
            "perplexity": result.perplexity,
            "avg_loss": result.avg_loss,
            "accuracy": result.accuracy,
            "num_tokens": result.num_tokens,
        }

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    async def _run_job(self, job: TrainingJob) -> None:
        cfg = job.config
        job.status = JobStatus.RUNNING
        job.logs.append(f"Job {cfg.job_id} started")
        try:
            version = self._datasets.get_latest_version(cfg.dataset_path, split="train")
            if version is None:
                raise ValueError(
                    f"Dataset '{cfg.dataset_path}' has no train split. "
                    "Ingest it first via POST /training/datasets."
                )

            tokenizer = self._loader.get_tokenizer(cfg.base_model_id)
            if tokenizer is None:
                self._loader.load(cfg.base_model_id)
                tokenizer = self._loader.get_tokenizer(cfg.base_model_id)

            preprocessor = Preprocessor(
                tokenizer,
                max_length=cfg.extra.get("max_length", 512),
                stride=cfg.extra.get("stride"),
            )
            chunks = preprocessor.process_samples(
                self._datasets.iter_samples(version, cfg.extra.get("text_field", "text"))
            )

            output_dir = await self._trainer.train(
                job_id=cfg.job_id,
                base_model_id=cfg.base_model_id,
                chunks=chunks,
                output_model_id=cfg.output_model_id,
                epochs=cfg.epochs,
                learning_rate=cfg.learning_rate,
                batch_size=cfg.batch_size,
                config={"base_model_id": cfg.base_model_id, "output_model_id": cfg.output_model_id},
            )

            if output_dir:
                self._signer.sign(Path(output_dir))
                self._loader.scan()  # re-scan so new model is available
                job.status = JobStatus.COMPLETED
                job.progress = 1.0
                job.logs.append(f"Output model: {output_dir}")
            else:
                job.status = JobStatus.CANCELLED

        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
        except Exception as exc:
            logger.error("Job '%s' failed: %s", cfg.job_id, exc, exc_info=True)
            job.status = JobStatus.FAILED
            job.logs.append(f"ERROR: {exc}")

    def _on_progress(self, job_id: str, progress: float, log_line: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.progress = progress
            job.logs.append(log_line)
