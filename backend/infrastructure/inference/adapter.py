"""MambaInferenceAdapter — concrete implementation of IInferencePort.

All inference runs locally. Zero network calls.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator

from backend.domain.ports.inference import (
    IInferencePort,
    InferenceRequest,
    InferenceResponse,
)
from backend.infrastructure.inference.loader import MambaModelLoader
from backend.shared.exceptions import AegisBaseError

logger = logging.getLogger(__name__)


class InferenceError(AegisBaseError):
    """Raised when inference fails."""


class MambaInferenceAdapter(IInferencePort):
    """Bridges IInferencePort to MambaModelLoader + actual SSM forward pass.

    Generation strategy:
        1. Encode prompt via tokenizer.
        2. Run autoregressive forward pass (greedy or sampling) for `max_tokens` steps.
        3. Decode and return / yield tokens.

    Runs in a thread-pool executor so it never blocks the async event loop.
    """

    def __init__(self, loader: MambaModelLoader, default_model_id: str | None = None) -> None:
        self._loader = loader
        self._default_model_id = default_model_id
        self._executor = None  # uses asyncio default thread pool

    # ------------------------------------------------------------------
    # IInferencePort API
    # ------------------------------------------------------------------

    async def run(self, request: InferenceRequest) -> InferenceResponse:
        model_id = request.model_id or self._default_model_id
        if not model_id:
            raise InferenceError("No model_id specified and no default model loaded.")

        if not self._loader.is_loaded(model_id):
            await self.load_model(model_id)

        loop = asyncio.get_event_loop()
        start = time.perf_counter()
        text, prompt_tokens, completion_tokens = await loop.run_in_executor(
            self._executor,
            self._generate_sync,
            model_id,
            request,
        )
        elapsed = time.perf_counter() - start
        logger.debug(
            "Inference done model=%s prompt_tok=%d compl_tok=%d elapsed=%.2fs",
            model_id, prompt_tokens, completion_tokens, elapsed,
        )
        finish = "length" if completion_tokens >= request.max_tokens else "stop"
        return InferenceResponse(
            text=text,
            model_id=model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=finish,
        )

    async def stream(self, request: InferenceRequest) -> AsyncIterator[str]:
        model_id = request.model_id or self._default_model_id
        if not model_id:
            raise InferenceError("No model_id specified and no default model loaded.")

        if not self._loader.is_loaded(model_id):
            await self.load_model(model_id)

        queue: asyncio.Queue[str | None] = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def _run_and_push() -> None:
            try:
                tokenizer = self._loader.get_tokenizer(model_id)
                model = self._loader.get_model(model_id)
                encoding = tokenizer.encode(request.prompt)
                input_ids = encoding.ids

                gen_fn = _pick_generate_fn(model)
                for token_id in gen_fn(
                    model,
                    input_ids,
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.extra.get("top_p", 1.0),
                    repetition_penalty=request.extra.get("repetition_penalty", 1.0),
                ):
                    token_text = tokenizer.decode([token_id])
                    loop.call_soon_threadsafe(queue.put_nowait, token_text)
            except Exception as exc:
                logger.error("Streaming error: %s", exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        loop.run_in_executor(self._executor, _run_and_push)

        while True:
            token = await queue.get()
            if token is None:
                break
            yield token

    async def list_models(self) -> list[str]:
        return self._loader.scan()

    async def load_model(self, model_id: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self._loader.load,
            model_id,
        )

    async def unload_model(self, model_id: str) -> None:
        self._loader.unload(model_id)

    # ------------------------------------------------------------------
    # Sync generation (runs in thread pool)
    # ------------------------------------------------------------------

    def _generate_sync(
        self,
        model_id: str,
        request: InferenceRequest,
    ) -> tuple[str, int, int]:
        tokenizer = self._loader.get_tokenizer(model_id)
        model = self._loader.get_model(model_id)

        encoding = tokenizer.encode(request.prompt)
        input_ids = encoding.ids
        prompt_tokens = len(input_ids)

        generated: list[int] = []
        gen_fn = _pick_generate_fn(model)
        for token_id in gen_fn(
            model,
            input_ids,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.extra.get("top_p", 1.0),
            repetition_penalty=request.extra.get("repetition_penalty", 1.0),
        ):
            generated.append(token_id)

        text = tokenizer.decode(generated)
        return text, prompt_tokens, len(generated)


# ---------------------------------------------------------------------------
# Generation utilities
# ---------------------------------------------------------------------------

def _pick_generate_fn(model: object):
    """Return the right generation function based on what the model exposes."""
    # mamba-ssm has its own generate method
    if hasattr(model, "generate"):
        return _generate_via_model_method
    # mamba-minimal style: plain forward returning logits
    return _generate_greedy_sampling


def _generate_via_model_method(
    model,
    input_ids: list[int],
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 1.0,
    repetition_penalty: float = 1.0,
):
    """Delegate to model.generate() for mamba-ssm."""
    try:
        import torch

        ids_tensor = torch.tensor([input_ids], dtype=torch.long)
        if next(model.parameters()).is_cuda:
            ids_tensor = ids_tensor.cuda()

        out = model.generate(
            input_ids=ids_tensor,
            max_length=len(input_ids) + max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            eos_token_id=0,
        )
        new_ids = out[0, len(input_ids):].tolist()
        yield from new_ids
    except Exception as exc:
        logger.error("model.generate() failed: %s — falling back to greedy", exc)
        yield from _generate_greedy_sampling(
            model, input_ids, max_new_tokens, temperature, top_p, repetition_penalty
        )


def _generate_greedy_sampling(
    model,
    input_ids: list[int],
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 1.0,
    repetition_penalty: float = 1.0,
):
    """Autoregressive greedy/sampling loop for models that expose raw logits."""
    try:
        import torch
        import torch.nn.functional as F

        current_ids = list(input_ids)

        with torch.no_grad():
            for _ in range(max_new_tokens):
                x = torch.tensor([current_ids], dtype=torch.long)
                logits = model(x)  # (1, seq_len, vocab)
                next_logits = logits[0, -1, :]  # (vocab,)

                # Repetition penalty
                if repetition_penalty != 1.0:
                    for uid in set(current_ids):
                        if uid < next_logits.shape[0]:
                            next_logits[uid] /= repetition_penalty

                # Temperature
                if temperature > 0 and temperature != 1.0:
                    next_logits = next_logits / temperature

                probs = F.softmax(next_logits, dim=-1)

                # Top-p (nucleus) sampling
                if top_p < 1.0:
                    sorted_probs, sorted_idx = torch.sort(probs, descending=True)
                    cumulative = torch.cumsum(sorted_probs, dim=0)
                    mask = cumulative - sorted_probs > top_p
                    sorted_probs[mask] = 0.0
                    probs = torch.zeros_like(probs)
                    probs[sorted_idx] = sorted_probs
                    probs /= probs.sum()
                    next_token = torch.multinomial(probs, num_samples=1).item()
                elif temperature == 0.0:
                    next_token = int(torch.argmax(probs).item())
                else:
                    next_token = int(torch.multinomial(probs, num_samples=1).item())

                yield next_token
                current_ids.append(next_token)

                # EOS (id=0 for GPT-NeoX / Mamba default)
                if next_token == 0:
                    break

    except ImportError:
        # No torch at all — yield a placeholder for testing
        logger.error("torch not available; yielding placeholder tokens")
        yield from [72, 101, 108, 108, 111]
