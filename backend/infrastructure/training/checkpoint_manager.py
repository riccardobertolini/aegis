"""Checkpoint manager — saves/loads model state dicts with SHA-256 signing."""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.domain.ports.training import CheckpointInfo

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Saves checkpoints under::

        experiments/<job_id>/checkpoints/step_<N>/
            model.pt
            meta.json      # CheckpointInfo + sha256
    """

    def __init__(self, experiments_root: Path) -> None:
        self._root = experiments_root

    def save(
        self,
        job_id: str,
        step: int,
        epoch: int,
        model: Any,
        train_loss: float,
        val_loss: float | None = None,
    ) -> CheckpointInfo:
        import torch  # type: ignore

        ckpt_dir = self._ckpt_dir(job_id, step)
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        weight_path = ckpt_dir / "model.pt"

        state = model.state_dict() if hasattr(model, "state_dict") else model
        torch.save(state, str(weight_path))

        sha256 = self._sha256(weight_path)
        info = CheckpointInfo(
            job_id=job_id,
            step=step,
            epoch=epoch,
            path=str(ckpt_dir),
            train_loss=train_loss,
            val_loss=val_loss,
            created_at=datetime.now(timezone.utc),
        )
        meta = {**asdict(info), "sha256": sha256}
        (ckpt_dir / "meta.json").write_text(json.dumps(meta, indent=2, default=str))
        logger.info("Checkpoint saved: job=%s step=%d sha256=%s…", job_id, step, sha256[:16])
        return info

    def load(self, job_id: str, step: int) -> tuple[Any, CheckpointInfo]:
        import torch  # type: ignore

        ckpt_dir = self._ckpt_dir(job_id, step)
        weight_path = ckpt_dir / "model.pt"
        if not weight_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {weight_path}")

        meta_raw = json.loads((ckpt_dir / "meta.json").read_text())
        stored_sha = meta_raw.get("sha256", "")
        actual_sha = self._sha256(weight_path)
        if stored_sha and stored_sha != actual_sha:
            raise ValueError(
                f"Checkpoint integrity failure at step {step}: "
                f"expected {stored_sha[:16]}… got {actual_sha[:16]}…"
            )

        state = torch.load(str(weight_path), map_location="cpu", weights_only=True)
        info = CheckpointInfo(
            job_id=meta_raw["job_id"],
            step=meta_raw["step"],
            epoch=meta_raw["epoch"],
            path=meta_raw["path"],
            train_loss=meta_raw["train_loss"],
            val_loss=meta_raw.get("val_loss"),
        )
        return state, info

    def list_checkpoints(self, job_id: str) -> list[CheckpointInfo]:
        job_dir = self._root / job_id / "checkpoints"
        if not job_dir.exists():
            return []
        infos: list[CheckpointInfo] = []
        for d in sorted(job_dir.iterdir()):
            meta_file = d / "meta.json"
            if not meta_file.exists():
                continue
            try:
                m = json.loads(meta_file.read_text())
                infos.append(
                    CheckpointInfo(
                        job_id=m["job_id"],
                        step=m["step"],
                        epoch=m["epoch"],
                        path=m["path"],
                        train_loss=m["train_loss"],
                        val_loss=m.get("val_loss"),
                    )
                )
            except Exception as exc:
                logger.warning("Cannot read checkpoint meta at %s: %s", d, exc)
        return infos

    def promote(
        self,
        job_id: str,
        step: int,
        models_root: Path,
        target_model_id: str,
    ) -> str:
        """Copy checkpoint weights + config into models/<target_model_id>/."""
        import shutil
        import torch  # type: ignore

        ckpt_dir = self._ckpt_dir(job_id, step)
        weight_src = ckpt_dir / "model.pt"
        if not weight_src.exists():
            raise FileNotFoundError(f"Checkpoint step {step} not found for job {job_id}")

        dest = models_root / target_model_id
        dest.mkdir(parents=True, exist_ok=True)

        shutil.copy2(str(weight_src), str(dest / "model.pt"))

        # copy config.json from experiment if present
        exp_config = self._root / job_id / "config.json"
        if exp_config.exists():
            raw = json.loads(exp_config.read_text())
            model_cfg = raw.get("extra", raw)
            model_cfg["model_type"] = model_cfg.get("model_type", "mamba")
            (dest / "config.json").write_text(json.dumps(model_cfg, indent=2))

        sha256 = self._sha256(dest / "model.pt")
        manifest = {
            "promoted_from_job": job_id,
            "promoted_from_step": step,
            "sha256": sha256,
            "target_model_id": target_model_id,
        }
        (dest / "promotion.json").write_text(json.dumps(manifest, indent=2))
        logger.info(
            "Model promoted: job=%s step=%d → models/%s (sha256=%s…)",
            job_id, step, target_model_id, sha256[:16],
        )
        return sha256

    # ------------------------------------------------------------------
    def _ckpt_dir(self, job_id: str, step: int) -> Path:
        return self._root / job_id / "checkpoints" / f"step_{step:08d}"

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
