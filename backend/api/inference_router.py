"""REST API router for inference and Core AI.

Endpoints:
    POST   /api/v1/inference/completions           — single completion
    POST   /api/v1/inference/completions/stream    — SSE streaming
    GET    /api/v1/inference/models                — list available models
    GET    /api/v1/inference/models/{model_id}     — model details
    POST   /api/v1/inference/models/{model_id}/load
    DELETE /api/v1/inference/models/{model_id}
    POST   /api/v1/ai/chat                         — CoreAI pipeline (full orchestration)
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.domain.ports.core_ai import AIRequest
from backend.domain.ports.inference import InferenceRequest

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CompletionRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=32_768)
    model_id: str = Field(default="")
    max_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    repetition_penalty: float = Field(default=1.0, ge=0.5, le=2.0)
    seed: int | None = Field(default=None)
    stream: bool = Field(default=False)


class CompletionResponse(BaseModel):
    text: str
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    user_input: str = Field(..., min_length=1, max_length=32_768)
    model_id: str = Field(default="")
    max_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    repetition_penalty: float = Field(default=1.0, ge=0.5, le=2.0)
    assistant_id: str = Field(default="default")
    user_id: str = Field(default="anonymous")


class ChatResponse(BaseModel):
    session_id: str
    text: str
    engine_trace: list[str]
    metadata: dict


class ModelInfo(BaseModel):
    model_id: str
    loaded: bool
    architecture: str = ""
    context_length: int = 0
    d_model: int = 0
    n_layer: int = 0
    vocab_size: int = 0


# ---------------------------------------------------------------------------
# Dependency: InferenceContainer from app state
# ---------------------------------------------------------------------------

def _get_inference_container(request: Request):
    container = getattr(request.app.state, "inference_container", None)
    if container is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference engine not initialised. Check server startup logs.",
        )
    return container


# ---------------------------------------------------------------------------
# Completions
# ---------------------------------------------------------------------------

@router.post(
    "/completions",
    response_model=CompletionResponse,
    summary="Run a single completion (non-streaming)",
)
async def completions(
    body: CompletionRequest,
    container=Depends(_get_inference_container),
) -> CompletionResponse:
    req = InferenceRequest(
        prompt=body.prompt,
        model_id=body.model_id,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        stream=False,
        extra={
            "top_p": body.top_p,
            "repetition_penalty": body.repetition_penalty,
            "seed": body.seed,
        },
    )
    try:
        resp = await container.inference.run(req)
    except Exception as exc:
        logger.error("Inference failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return CompletionResponse(
        text=resp.text,
        model_id=resp.model_id,
        prompt_tokens=resp.prompt_tokens,
        completion_tokens=resp.completion_tokens,
        finish_reason=resp.finish_reason,
    )


@router.post(
    "/completions/stream",
    summary="Stream tokens via SSE",
    response_class=StreamingResponse,
)
async def completions_stream(
    body: CompletionRequest,
    container=Depends(_get_inference_container),
) -> StreamingResponse:
    req = InferenceRequest(
        prompt=body.prompt,
        model_id=body.model_id,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        stream=True,
        extra={
            "top_p": body.top_p,
            "repetition_penalty": body.repetition_penalty,
        },
    )

    async def _sse_generator() -> AsyncIterator[str]:
        try:
            async for token in container.inference.stream(req):
                # SSE format: "data: <token>\n\n"
                yield f"data: {token}\n\n"
        except Exception as exc:
            logger.error("Streaming error: %s", exc)
            yield f"event: error\ndata: {exc}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Models management
# ---------------------------------------------------------------------------

@router.get(
    "/models",
    response_model=list[ModelInfo],
    summary="List all locally available SSM models",
)
async def list_models(
    container=Depends(_get_inference_container),
) -> list[ModelInfo]:
    available = await container.inference.list_models()
    result: list[ModelInfo] = []
    for mid in available:
        meta = container.loader.get_meta(mid)
        result.append(ModelInfo(
            model_id=mid,
            loaded=container.loader.is_loaded(mid),
            architecture=meta.architecture if meta else "",
            context_length=meta.context_length if meta else 0,
            d_model=meta.d_model if meta else 0,
            n_layer=meta.n_layer if meta else 0,
            vocab_size=meta.vocab_size if meta else 0,
        ))
    return result


@router.get(
    "/models/{model_id}",
    response_model=ModelInfo,
    summary="Get details of a specific model",
)
async def get_model(
    model_id: str,
    container=Depends(_get_inference_container),
) -> ModelInfo:
    meta = container.loader.get_meta(model_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    return ModelInfo(
        model_id=model_id,
        loaded=container.loader.is_loaded(model_id),
        architecture=meta.architecture,
        context_length=meta.context_length,
        d_model=meta.d_model,
        n_layer=meta.n_layer,
        vocab_size=meta.vocab_size,
    )


@router.post(
    "/models/{model_id}/load",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Load a model into memory",
)
async def load_model(
    model_id: str,
    container=Depends(_get_inference_container),
) -> dict:
    try:
        await container.inference.load_model(model_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "loaded", "model_id": model_id}


@router.delete(
    "/models/{model_id}",
    status_code=status.HTTP_200_OK,
    summary="Unload a model from memory",
)
async def unload_model(
    model_id: str,
    container=Depends(_get_inference_container),
) -> dict:
    await container.inference.unload_model(model_id)
    return {"status": "unloaded", "model_id": model_id}


# ---------------------------------------------------------------------------
# CoreAI chat
# ---------------------------------------------------------------------------

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Full CoreAI pipeline: intent → memory → inference → memory",
)
async def chat(
    body: ChatRequest,
    container=Depends(_get_inference_container),
) -> ChatResponse:
    ai_request = AIRequest(
        session_id=body.session_id,
        user_input=body.user_input,
        context={
            "model_id": body.model_id,
            "max_tokens": body.max_tokens,
            "temperature": body.temperature,
            "top_p": body.top_p,
            "repetition_penalty": body.repetition_penalty,
            "assistant_id": body.assistant_id,
            "user_id": body.user_id,
        },
    )
    try:
        resp = await container.core_ai.process(ai_request)
    except Exception as exc:
        logger.error("CoreAI pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        session_id=resp.session_id,
        text=resp.text,
        engine_trace=resp.engine_trace,
        metadata=resp.metadata,
    )
