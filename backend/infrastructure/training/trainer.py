"""MambaTrainer — fine-tuning loop for SSM/Mamba models.

Supports:
  - GPU path via mamba-ssm (CUDA)
  - CPU path via mamba-minimal (pure Python)
  - Cancellation via threading.Event
  - Gradient clipping, linear LR warmup, checkpoint at N steps
  - Evaluation loss on val set every M steps
"""
from __future__ import annotations

import logging
import math
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.domain.ports.training import (
    CheckpointInfo,
    ExperimentMetrics,
    TrainingConfig,
)
from backend.infrastructure.training.checkpoint_manager import CheckpointManager
from backend.infrastructure.training.experiment_tracker import ExperimentTracker
from backend.infrastructure.training.preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)


class MambaTrainer:
    """
    Fine-tunes a Mamba/SSM model on a list of token sequences.
    Called from TrainingService in a background thread.
    """

    def __init__(
        self,
        config: TrainingConfig,
        model: Any,
        tokenizer: Any,
        tracker: ExperimentTracker,
        ckpt_manager: CheckpointManager,
        cancel_event: threading.Event,
        on_progress: Callable[[float, int, int], None] | None = None,
    ) -> None:
        self._cfg = config
        self._model = model
        self._tokenizer = tokenizer
        self._tracker = tracker
        self._ckpt_manager = ckpt_manager
        self._cancel = cancel_event
        self._on_progress = on_progress
        self._preprocessor = TextPreprocessor(tokenizer, max_seq_len=config.max_seq_len)

    def run(
        self,
        train_texts: list[str],
        val_texts: list[str],
    ) -> dict:
        """
        Execute the training loop.
        Returns a summary dict: {best_val_loss, final_train_loss, total_steps}.
        """
        import torch  # type: ignore
        import torch.nn as nn
        import torch.optim as optim

        cfg = self._cfg
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Training on device: %s", device)

        model = self._model
        try:
            model = model.to(device)
        except Exception:
            pass  # mamba-minimal models may not support .to()

        model.train()
        optimizer = optim.AdamW(
            model.parameters(),
            lr=cfg.learning_rate,
            weight_decay=0.01,
        )

        # LR scheduler: linear warmup then constant
        def lr_lambda(step: int) -> float:
            if cfg.warmup_steps > 0 and step < cfg.warmup_steps:
                return float(step) / float(max(1, cfg.warmup_steps))
            return 1.0

        scheduler = optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

        train_seqs = self._preprocessor.tokenize(train_texts)
        val_seqs = self._preprocessor.tokenize(val_texts) if val_texts else []

        if not train_seqs:
            raise ValueError("No training sequences after tokenisation.")

        total_steps = cfg.epochs * math.ceil(len(train_seqs) / cfg.batch_size)
        global_step = 0
        best_val_loss: float | None = None
        last_train_loss: float = 0.0

        for epoch in range(cfg.epochs):
            if self._cancel.is_set():
                break

            batches = list(self._preprocessor.make_batches(train_seqs, cfg.batch_size))

            for batch in batches:
                if self._cancel.is_set():
                    break

                t0 = time.perf_counter()
                loss, n_tokens = self._train_step(model, optimizer, batch, device)
                scheduler.step()
                t1 = time.perf_counter()

                nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)

                global_step += 1
                last_train_loss = loss
                elapsed = max(t1 - t0, 1e-9)
                tok_per_sec = n_tokens / elapsed

                metrics = ExperimentMetrics(
                    job_id=cfg.job_id,
                    step=global_step,
                    epoch=epoch,
                    train_loss=loss,
                    learning_rate=scheduler.get_last_lr()[0],
                    tokens_per_second=tok_per_sec,
                )

                # Eval
                val_loss: float | None = None
                if (
                    val_seqs
                    and cfg.eval_every_n_steps > 0
                    and global_step % cfg.eval_every_n_steps == 0
                ):
                    val_loss = self._eval_loss(model, val_seqs, device, cfg.batch_size)
                    metrics.val_loss = val_loss
                    if best_val_loss is None or val_loss < best_val_loss:
                        best_val_loss = val_loss

                self._tracker.log_metrics(metrics)

                if self._on_progress:
                    self._on_progress(
                        global_step / total_steps,
                        global_step,
                        epoch,
                    )

                # Checkpoint
                if (
                    cfg.save_every_n_steps > 0
                    and global_step % cfg.save_every_n_steps == 0
                ):
                    self._ckpt_manager.save(
                        cfg.job_id, global_step, epoch, model,
                        last_train_loss, val_loss,
                    )

        # Final checkpoint
        self._ckpt_manager.save(
            cfg.job_id, global_step, cfg.epochs - 1, model,
            last_train_loss, None,
        )

        summary = {
            "job_id": cfg.job_id,
            "total_steps": global_step,
            "final_train_loss": last_train_loss,
            "best_val_loss": best_val_loss,
            "cancelled": self._cancel.is_set(),
        }
        self._tracker.write_summary(cfg.job_id, summary)
        return summary

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _train_step(
        self,
        model: Any,
        optimizer: Any,
        batch: list[list[int]],
        device: str,
    ) -> tuple[float, int]:
        import torch
        import torch.nn.functional as F

        optimizer.zero_grad()
        # Pad batch to same length
        max_len = max(len(s) for s in batch)
        input_ids = torch.zeros(len(batch), max_len, dtype=torch.long, device=device)
        for i, seq in enumerate(batch):
            input_ids[i, : len(seq)] = torch.tensor(seq, dtype=torch.long)

        labels = input_ids.clone()
        labels[:, :-1] = input_ids[:, 1:]   # next-token prediction
        labels[:, -1] = -100                 # ignore last

        try:
            out = model(input_ids)  # (B, L, vocab)
            logits = out.logits if hasattr(out, "logits") else out
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                labels.view(-1),
                ignore_index=-100,
            )
        except Exception as exc:
            logger.warning("Train step error: %s — skipping batch", exc)
            return 0.0, 0

        loss.backward()
        n_tokens = int((labels != -100).sum().item())
        return float(loss.item()), n_tokens

    def _eval_loss(
        self,
        model: Any,
        val_seqs: list[list[int]],
        device: str,
        batch_size: int,
    ) -> float:
        import torch
        import torch.nn.functional as F

        model.eval()
        total_loss = 0.0
        n_batches = 0
        with torch.no_grad():
            for batch in self._preprocessor.make_batches(val_seqs, batch_size):
                max_len = max(len(s) for s in batch)
                input_ids = torch.zeros(len(batch), max_len, dtype=torch.long, device=device)
                for i, seq in enumerate(batch):
                    input_ids[i, : len(seq)] = torch.tensor(seq, dtype=torch.long)
                labels = input_ids.clone()
                labels[:, :-1] = input_ids[:, 1:]
                labels[:, -1] = -100
                try:
                    out = model(input_ids)
                    logits = out.logits if hasattr(out, "logits") else out
                    loss = F.cross_entropy(
                        logits.view(-1, logits.size(-1)),
                        labels.view(-1),
                        ignore_index=-100,
                    )
                    total_loss += float(loss.item())
                    n_batches += 1
                except Exception:
                    pass
        model.train()
        return total_loss / max(n_batches, 1)
