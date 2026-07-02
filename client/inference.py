"""Inference API client methods."""
from __future__ import annotations

from .base import AegisClient


class InferenceMixin(AegisClient):
    """Methods for /api/v1/inference endpoints."""

    BASE = "/api/v1/inference"

    def list_models(self) -> list[dict]:
        """GET /api/v1/inference/models"""
        return self._get(f"{self.BASE}/models")

    def get_model(self, model_id: str) -> dict:
        """GET /api/v1/inference/models/{model_id}"""
        return self._get(f"{self.BASE}/models/{model_id}")

    def load_model(self, model_id: str) -> dict:
        """POST /api/v1/inference/models/{model_id}/load"""
        return self._post(f"{self.BASE}/models/{model_id}/load")

    def unload_model(self, model_id: str) -> None:
        """DELETE /api/v1/inference/models/{model_id}"""
        self._delete(f"{self.BASE}/models/{model_id}")

    def complete(
        self,
        prompt: str,
        model_id: str = "",
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0,
        seed: int | None = None,
    ) -> dict:
        """POST /api/v1/inference/completions"""
        return self._post(
            f"{self.BASE}/completions",
            json={
                "prompt": prompt,
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "repetition_penalty": repetition_penalty,
                "seed": seed,
                "stream": False,
            },
        )

    def chat(
        self,
        session_id: str,
        user_input: str,
        model_id: str = "",
        max_tokens: int = 512,
        temperature: float = 0.7,
        assistant_id: str = "default",
        user_id: str = "anonymous",
    ) -> dict:
        """POST /api/v1/ai/chat — full CoreAI pipeline"""
        return self._post(
            "/api/v1/ai/chat",
            json={
                "session_id": session_id,
                "user_input": user_input,
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "assistant_id": assistant_id,
                "user_id": user_id,
            },
        )
