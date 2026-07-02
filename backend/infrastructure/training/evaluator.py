"""Evaluator: compute perplexity and token accuracy on an eval split."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    perplexity: float
    avg_loss: float
    accuracy: float   # token-level top-1 accuracy
    num_tokens: int


class Evaluator:
    """Runs evaluation (perplexity + accuracy) on a list of token chunks.

    Parameters
    ----------
    model:
        Loaded Mamba/SSM model (same object returned by MambaModelLoader).
    """

    def __init__(self, model: Any) -> None:
        self._model = model

    def evaluate(self, chunks: list[list[int]], batch_size: int = 4) -> EvalResult:
        try:
            import torch
            import torch.nn.functional as F
        except ImportError as exc:
            raise ImportError("PyTorch required for evaluation.") from exc

        model = self._model
        model.eval()
        device = next(model.parameters()).device

        total_loss = 0.0
        total_correct = 0
        total_tokens = 0
        n_batches = 0

        with torch.no_grad():
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]
                ids = torch.tensor(batch, dtype=torch.long, device=device)
                inp = ids[:, :-1]
                tgt = ids[:, 1:]

                try:
                    logits = model(inp)
                    if hasattr(logits, "logits"):
                        logits = logits.logits
                    vocab = logits.size(-1)
                    loss = F.cross_entropy(
                        logits.reshape(-1, vocab),
                        tgt.reshape(-1),
                        ignore_index=0,
                        reduction="sum",
                    )
                    preds = logits.argmax(dim=-1)
                    mask = tgt != 0
                    correct = (preds == tgt).masked_select(mask).sum().item()
                    tokens = mask.sum().item()

                    total_loss += loss.item()
                    total_correct += correct
                    total_tokens += tokens
                    n_batches += 1
                except Exception as exc:
                    logger.warning("Eval batch error: %s", exc)

        if total_tokens == 0:
            return EvalResult(perplexity=float("inf"), avg_loss=float("inf"), accuracy=0.0, num_tokens=0)

        avg_loss = total_loss / total_tokens
        perplexity = math.exp(min(avg_loss, 20))  # clip to avoid overflow
        accuracy = total_correct / total_tokens
        logger.info("Eval — ppl=%.2f loss=%.4f acc=%.4f tokens=%d", perplexity, avg_loss, accuracy, total_tokens)
        return EvalResult(perplexity=perplexity, avg_loss=avg_loss, accuracy=accuracy, num_tokens=total_tokens)
