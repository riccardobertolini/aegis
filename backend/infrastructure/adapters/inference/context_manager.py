"""ContextManager — rolling context window with compression and incremental summarisation.

Mamba/SSM context design:
- Mamba processes sequences with O(L) memory, but very long inputs still
  increase latency. This module keeps the effective context within
  `max_context_length` tokens by:
  1. Importance scoring: tokens near the end + high TF-IDF scored tokens
     are kept; low-importance middle tokens are dropped.
  2. Incremental summarisation: every N tokens, a short summary of the
     dropped portion is prepended as a system prefix.

This module is pure Python (no torch) and testable without weights.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from backend.domain.model.runtime_config import RuntimeConfig


@dataclass
class ContextWindow:
    """Holds the current token context for a session."""
    session_id: str
    tokens: list[int] = field(default_factory=list)
    summary_prefix: list[int] = field(default_factory=list)  # compressed history
    total_tokens_processed: int = 0

    def effective_length(self) -> int:
        return len(self.summary_prefix) + len(self.tokens)


class ContextManager:
    """
    Manages per-session rolling context windows.

    ``append`` adds new tokens; if the window exceeds max_context_length,
    compression is triggered automatically.
    """

    def __init__(self) -> None:
        self._windows: dict[str, ContextWindow] = {}

    def get_or_create(self, session_id: str) -> ContextWindow:
        if session_id not in self._windows:
            self._windows[session_id] = ContextWindow(session_id=session_id)
        return self._windows[session_id]

    def append(self, session_id: str, new_tokens: list[int], config: RuntimeConfig) -> ContextWindow:
        """Append tokens and compress if needed."""
        window = self.get_or_create(session_id)
        window.tokens.extend(new_tokens)
        window.total_tokens_processed += len(new_tokens)

        if config.enable_context_compression and window.effective_length() > config.max_context_length:
            window = self._compress(window, config)

        return window

    def build_prompt_ids(self, session_id: str) -> list[int]:
        """Return the full token sequence (summary_prefix + recent tokens)."""
        window = self.get_or_create(session_id)
        return window.summary_prefix + window.tokens

    def clear(self, session_id: str) -> None:
        self._windows.pop(session_id, None)

    # ------------------------------------------------------------------
    # Compression
    # ------------------------------------------------------------------

    @staticmethod
    def _compress(window: ContextWindow, config: RuntimeConfig) -> ContextWindow:
        """
        Drop low-importance tokens from the middle of the context.

        Strategy:
        - Always keep the first 5% (system prompt region) and last 30% (recent context).
        - Score middle tokens by TF-IDF-like frequency: rare tokens carry more information.
        - Keep top `compression_ratio` fraction of middle tokens by score.
        - The dropped portion is represented by a stub summary_prefix (list of special IDs).
          In production the Inference Engine would run a summarisation forward pass here.
        """
        tokens = window.tokens
        n = len(tokens)
        keep_head = max(1, int(n * 0.05))
        keep_tail = max(1, int(n * 0.30))
        middle = tokens[keep_head: n - keep_tail]

        if not middle:
            return window

        scores = ContextManager._score_tokens(middle)
        keep_n = max(1, int(len(middle) * config.compression_ratio))
        top_indices = sorted(
            range(len(middle)),
            key=lambda i: scores[i],
            reverse=True,
        )[:keep_n]
        top_indices_set = set(top_indices)
        kept_middle = [t for i, t in enumerate(middle) if i in top_indices_set]

        # Build compressed summary prefix (placeholder: first 16 tokens of dropped region)
        dropped = [t for i, t in enumerate(middle) if i not in top_indices_set]
        window.summary_prefix = dropped[:16]  # stub; replaced by real summarisation in later phase
        window.tokens = tokens[:keep_head] + kept_middle + tokens[n - keep_tail:]
        return window

    @staticmethod
    def _score_tokens(tokens: list[int]) -> list[float]:
        """
        Score tokens by inverse frequency (rare = more important).
        Returns a score list parallel to *tokens*.
        """
        counts = Counter(tokens)
        total = len(tokens)
        scores: list[float] = []
        for t in tokens:
            tf = counts[t] / total
            idf = math.log(1.0 + 1.0 / (tf + 1e-9))
            scores.append(idf)
        return scores
