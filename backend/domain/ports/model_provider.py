"""Port: ModelProvider — abstraction over any SSM backend.

This port separates the *what* (generate tokens) from the *how*
(Mamba-SSM CUDA, mamba-minimal CPU, future alternatives).
The InferenceEngine uses only this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from backend.domain.model.model_metadata import ModelMetadata
from backend.domain.model.runtime_config import RuntimeConfig


class IModelProvider(ABC):
    """
    Low-level contract for a model backend.

    Responsibilities:
    - Load / unload model weights from disk (NO network calls ever)
    - Run a single forward pass (generate)
    - Stream tokens one by one
    - Report whether a model is currently loaded
    """

    @abstractmethod
    async def load(self, metadata: ModelMetadata, config: RuntimeConfig) -> None:
        """Load model weights into memory from local disk."""
        ...

    @abstractmethod
    async def unload(self, model_id: str) -> None:
        """Release model weights from memory."""
        ...

    @abstractmethod
    def is_loaded(self, model_id: str) -> bool:
        """Return True if model_id is currently in memory."""
        ...

    @abstractmethod
    async def generate(
        self,
        model_id: str,
        prompt_ids: list[int],
        config: RuntimeConfig,
    ) -> list[int]:
        """
        Run a full autoregressive decode.

        Args:
            model_id:   which loaded model to use
            prompt_ids: tokenised prompt as integer IDs
            config:     runtime knobs (temperature, max_new_tokens, …)

        Returns:
            list of generated token IDs (excluding prompt)
        """
        ...

    @abstractmethod
    async def stream_generate(
        self,
        model_id: str,
        prompt_ids: list[int],
        config: RuntimeConfig,
    ) -> AsyncIterator[int]:
        """
        Yield one token ID at a time during autoregressive decode.

        Useful for streaming responses to the API layer.
        """
        ...

    @abstractmethod
    async def encode(self, model_id: str, text: str) -> list[int]:
        """Tokenise *text* using the model's local tokenizer."""
        ...

    @abstractmethod
    async def decode(self, model_id: str, token_ids: list[int]) -> str:
        """Decode token IDs back to a string."""
        ...
