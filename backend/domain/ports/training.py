"""Port: Training Engine (esteso per Fase 8)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TrainingConfig:
    job_id: str
    base_model_id: str
    dataset_path: str
    output_model_id: str
    epochs: int = 3
    learning_rate: float = 1e-4
    batch_size: int = 8
    max_seq_len: int = 512
    grad_clip: float = 1.0
    warmup_steps: int = 0
    save_every_n_steps: int = 100
    eval_every_n_steps: int = 50
    seed: int = 42
    extra: dict = field(default_factory=dict)


@dataclass
class CheckpointInfo:
    job_id: str
    step: int
    epoch: int
    path: str
    train_loss: float
    val_loss: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ExperimentMetrics:
    job_id: str
    step: int
    epoch: int
    train_loss: float
    val_loss: float | None = None
    learning_rate: float = 0.0
    tokens_per_second: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TrainingJob:
    config: TrainingConfig
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    current_step: int = 0
    current_epoch: int = 0
    best_val_loss: float | None = None
    output_model_path: str | None = None
    model_sha256: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    logs: list[str] = field(default_factory=list)
    checkpoints: list[CheckpointInfo] = field(default_factory=list)


class ITrainingPort(ABC):
    """Contract for local fine-tuning / continual learning."""

    @abstractmethod
    async def start_job(self, config: TrainingConfig) -> TrainingJob: ...

    @abstractmethod
    async def get_job(self, job_id: str) -> TrainingJob: ...

    @abstractmethod
    async def cancel_job(self, job_id: str) -> None: ...

    @abstractmethod
    async def list_jobs(self) -> list[TrainingJob]: ...

    @abstractmethod
    async def get_metrics(self, job_id: str) -> list[ExperimentMetrics]: ...

    @abstractmethod
    async def list_checkpoints(self, job_id: str) -> list[CheckpointInfo]: ...

    @abstractmethod
    async def promote_checkpoint(
        self, job_id: str, step: int, target_model_id: str
    ) -> str: ...
