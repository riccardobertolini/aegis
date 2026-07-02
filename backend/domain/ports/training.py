"""Port: Training Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class JobStatus(str, Enum):
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
    extra: dict = field(default_factory=dict)


@dataclass
class TrainingJob:
    config: TrainingConfig
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    logs: list[str] = field(default_factory=list)


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
