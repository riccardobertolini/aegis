"""InferenceContainer — DI factory for the inference stack."""
from __future__ import annotations

from pathlib import Path

from backend.domain.ports.core_ai import ICoreAIPort
from backend.domain.ports.inference import IInferencePort
from backend.domain.ports.intent import IIntentPort
from backend.domain.ports.memory import IMemoryPort
from backend.infrastructure.inference.adapter import MambaInferenceAdapter
from backend.infrastructure.inference.core_ai import CoreAIService
from backend.infrastructure.inference.loader import MambaModelLoader


class InferenceContainer:
    """Wires loader → adapter → core_ai service.

    Usage::

        container = InferenceContainer.build(settings)
        inference_port: IInferencePort = container.inference
        core_ai_port: ICoreAIPort = container.core_ai
    """

    def __init__(
        self,
        loader: MambaModelLoader,
        inference: MambaInferenceAdapter,
        core_ai: CoreAIService,
    ) -> None:
        self._loader = loader
        self._inference = inference
        self._core_ai = core_ai

    @property
    def inference(self) -> IInferencePort:
        return self._inference

    @property
    def core_ai(self) -> ICoreAIPort:
        return self._core_ai

    @property
    def loader(self) -> MambaModelLoader:
        return self._loader

    @classmethod
    def build(
        cls,
        models_root: str | Path,
        default_model_id: str = "",
        system_prompt: str = "You are Aegis, a helpful AI assistant running fully offline.",
        max_context_turns: int = 10,
        memory: IMemoryPort | None = None,
        intent: IIntentPort | None = None,
    ) -> InferenceContainer:
        """Build and return a fully wired InferenceContainer.

        Args:
            models_root:      Absolute path to the models directory (e.g. BASE_DIR/models).
            default_model_id: Model to use when no model_id is specified in requests.
            system_prompt:    System prompt prepended to every conversation.
            max_context_turns: How many past turns to include in the prompt.
            memory:           Optional IMemoryPort implementation (injected).
            intent:           Optional IIntentPort implementation (injected).
        """
        loader = MambaModelLoader(models_root)
        loader.scan()

        # Auto-select default model if not specified
        available = loader.list_available()
        if not default_model_id and available:
            default_model_id = available[0]

        adapter = MambaInferenceAdapter(
            loader=loader,
            default_model_id=default_model_id or None,
        )
        core_ai = CoreAIService(
            inference=adapter,
            memory=memory,
            intent=intent,
            default_model_id=default_model_id,
            system_prompt=system_prompt,
            max_context_turns=max_context_turns,
        )
        return cls(loader=loader, inference=adapter, core_ai=core_ai)
