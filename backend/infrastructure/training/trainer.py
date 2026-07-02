"""Local SSM trainer — fine-tuning Mamba/mamba-minimal on CPU or GPU.

No cloud, no W&B, no HuggingFace hub calls.  Pure PyTorch training loop.
Supports both mamba-ssm (CUDA) and mamba-minimal (CPU) backends.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from backend.infrastructure.training.experiment import ExperimentTracker, MetricPoint
from backend.infrastructure.training.checkpoint import CheckpointManager

logger = logging.getLogger(__name__)


class LocalTrainer:
    """Fine-tunes a Mamba model on a list of token-id chunks.

    Parameters
    ----------
    model_loader:
        ``MambaModelLoader`` instance (from inference/loader.py).
    checkpoint_manager:
        ``CheckpointManager`` instance.
    tracker:
        ``ExperimentTracker`` instance.
    models_root:
        Root directory where models live (e.g. ``Path('models')``).
    on_progress:
        Optional callback ``(job_id, progress_float, log_line)``.
    """

    def __init__(
        self,
        model_loader: Any,
        checkpoint_manager: CheckpointManager,
        tracker: ExperimentTracker,
        models_root: Path,
        on_progress: Callable[[str, float, str], None] | None = None,
    ) -> None:
        self._loader = model_loader
        self._ckpt = checkpoint_manager
        self._tracker = tracker
        self._models_root = models_root
        self._on_progress = on_progress
        self._cancelled: set[str] = set()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def cancel(self, job_id: str) -> None:
        self._cancelled.add(job_id)

    async def train(
        self,
        job_id: str,
        base_model_id: str,
        chunks: list[list[int]],
        output_model_id: str,
        epochs: int = 3,
        learning_rate: float = 1e-4,
        batch_size: int = 4,
        save_every_n_steps: int = 50,
        config: dict | None = None,
    ) -> str:
        """Run training loop. Returns path of the output model directory."""
        run_id = f"{job_id}_{uuid.uuid4().hex[:8]}"
        cfg = config or {
            "base_model_id": base_model_id,
            "output_model_id": output_model_id,
            "epochs": epochs,
            "lr": learning_rate,
            "batch_size": batch_size,
        }
        self._tracker.start_run(run_id, job_id, cfg)

        try:
            import torch
            import torch.nn as nn
        except ImportError as exc:
            raise ImportError("PyTorch is required for training. See requirements/ml.txt.") from exc

        # Load base model
        model = self._loader.load(base_model_id)
        model.train()
        device = next(model.parameters()).device if hasattr(model, "parameters") else torch.device("cpu")

        optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=max(1, len(chunks) * epochs // batch_size)
        )

        total_steps = 0
        start = time.time()
        total_batches = max(1, len(chunks) // batch_size) * epochs

        for epoch in range(epochs):
            if job_id in self._cancelled:
                break

            batches = self._make_batches(chunks, batch_size)
            for batch_idx, batch in enumerate(batches):
                if job_id in self._cancelled:
                    break

                loss = self._train_step(model, batch, device, nn)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                total_steps += 1

                lr_now = scheduler.get_last_lr()[0]
                elapsed = time.time() - start
                point = MetricPoint(
                    step=total_steps,
                    epoch=epoch,
                    loss=loss,
                    lr=lr_now,
                    elapsed_s=elapsed,
                )
                self._tracker.log_metric(run_id, point)

                progress = total_steps / total_batches
                log_line = f"epoch={epoch} step={total_steps} loss={loss:.4f} lr={lr_now:.2e}"
                if self._on_progress:
                    self._on_progress(job_id, min(progress, 1.0), log_line)

                if total_steps % save_every_n_steps == 0:
                    self._ckpt.save(model, run_id, total_steps, {"loss": loss})

                # Yield control every batch so the event loop stays alive
                await asyncio.sleep(0)

        cancelled = job_id in self._cancelled
        self._cancelled.discard(job_id)

        if not cancelled:
            output_dir = self._promote_to_model(
                model, base_model_id, output_model_id, run_id, device, torch
            )
            self._tracker.finish_run(run_id, "completed")
            logger.info("Training complete — output: %s", output_dir)
            return output_dir
        else:
            self._tracker.finish_run(run_id, "cancelled")
            return ""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_batches(chunks: list[list[int]], batch_size: int) -> list[list[list[int]]]:
        return [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]

    @staticmethod
    def _train_step(model: Any, batch: list[list[int]], device: Any, nn: Any) -> float:
        import torch
        try:
            ids = torch.tensor(batch, dtype=torch.long, device=device)
            # Causal LM: input = ids[:,:-1], target = ids[:,1:]
            inp = ids[:, :-1]
            tgt = ids[:, 1:]
            logits = model(inp)  # (B, T, vocab_size)
            if hasattr(logits, "logits"):
                logits = logits.logits
            vocab = logits.size(-1)
            loss = nn.functional.cross_entropy(
                logits.reshape(-1, vocab),
                tgt.reshape(-1),
                ignore_index=0,
            )
            loss.backward()
            return loss.item()
        except Exception as exc:
            logger.warning("Train step error: %s", exc)
            return 0.0

    def _promote_to_model(
        self,
        model: Any,
        base_model_id: str,
        output_model_id: str,
        run_id: str,
        device: Any,
        torch: Any,
    ) -> str:
        import json
        import shutil

        output_dir = self._models_root / output_model_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save weights
        torch.save(model.state_dict(), str(output_dir / "model.pt"))

        # Copy config.json from base model
        base_config = self._models_root / base_model_id / "config.json"
        if base_config.exists():
            shutil.copy2(base_config, output_dir / "config.json")
        else:
            with open(output_dir / "config.json", "w") as f:
                json.dump({"model_type": "mamba", "fine_tuned_from": base_model_id}, f)

        # Copy tokenizer if present
        base_tok = self._models_root / base_model_id / "tokenizer.json"
        if base_tok.exists():
            shutil.copy2(base_tok, output_dir / "tokenizer.json")

        # Write training provenance
        with open(output_dir / "training_info.json", "w") as f:
            json.dump({
                "base_model_id": base_model_id,
                "run_id": run_id,
                "output_model_id": output_model_id,
            }, f, indent=2)

        logger.info("Model promoted to '%s'", output_dir)
        return str(output_dir)
