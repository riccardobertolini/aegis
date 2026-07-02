"""Training API client methods."""
from __future__ import annotations

from .base import AegisClient


class TrainingMixin(AegisClient):
    """Methods for /training endpoints."""

    BASE = "/training"

    def start_job(
        self,
        base_model_id: str,
        dataset_name: str,
        output_model_id: str,
        epochs: int = 3,
        learning_rate: float = 1e-4,
        batch_size: int = 4,
        max_length: int = 512,
        text_field: str = "text",
    ) -> dict:
        """POST /training/jobs"""
        return self._post(
            f"{self.BASE}/jobs",
            json={
                "base_model_id": base_model_id,
                "dataset_name": dataset_name,
                "output_model_id": output_model_id,
                "epochs": epochs,
                "learning_rate": learning_rate,
                "batch_size": batch_size,
                "max_length": max_length,
                "text_field": text_field,
            },
        )

    def list_jobs(self) -> list[dict]:
        """GET /training/jobs"""
        return self._get(f"{self.BASE}/jobs")

    def get_job(self, job_id: str) -> dict:
        """GET /training/jobs/{job_id}"""
        return self._get(f"{self.BASE}/jobs/{job_id}")

    def cancel_job(self, job_id: str) -> None:
        """DELETE /training/jobs/{job_id}"""
        self._delete(f"{self.BASE}/jobs/{job_id}")

    def list_datasets(self) -> dict:
        """GET /training/datasets"""
        return self._get(f"{self.BASE}/datasets")

    def ingest_dataset(self, name: str, source_path: str, split: str = "train", text_field: str = "text") -> dict:
        """POST /training/datasets"""
        return self._post(
            f"{self.BASE}/datasets",
            json={"name": name, "source_path": source_path, "split": split, "text_field": text_field},
        )

    def list_experiments(self) -> dict:
        """GET /training/experiments"""
        return self._get(f"{self.BASE}/experiments")

    def get_metrics(self, run_id: str) -> dict:
        """GET /training/experiments/{run_id}/metrics"""
        return self._get(f"{self.BASE}/experiments/{run_id}/metrics")

    def list_checkpoints(self, run_id: str) -> dict:
        """GET /training/checkpoints/{run_id}"""
        return self._get(f"{self.BASE}/checkpoints/{run_id}")

    def sign_model(self, model_id: str) -> dict:
        """POST /training/models/{model_id}/sign"""
        return self._post(f"{self.BASE}/models/{model_id}/sign")

    def verify_model(self, model_id: str) -> dict:
        """GET /training/models/{model_id}/verify"""
        return self._get(f"{self.BASE}/models/{model_id}/verify")
