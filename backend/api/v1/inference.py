"""FastAPI router: /api/v1/inference.

All endpoints are local-only. No HTTP calls to external hosts.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.domain.ports.inference import InferenceRequest, InferenceResponse
from backend.shared.exceptions import InferenceError, ModelLoadError, ModelNotFoundError

router = APIRouter(prefix="/api/v1/inference", tags=["inference"])


# --- Request / Response schemas ---

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=32_768)
    model_id: str = Field(default="default")
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = Field(default=False)
    session_id: str | None = Field(default=None)


class GenerateResponse(BaseModel):
    text: str
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str


class ModelListResponse(BaseModel):
    models: list[str]


# --- Dependency placeholder (wired in main.py in later phases) ---

def _get_inference_engine():
    """Dependency injector — replaced by real DI in main.py."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Inference engine not yet initialised.",
    )


# --- Endpoints ---

@router.get("/models", response_model=ModelListResponse)
async def list_models(engine=Depends(_get_inference_engine)) -> ModelListResponse:
    """Return IDs of all locally available models."""
    models = await engine.list_models()
    return ModelListResponse(models=models)


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    body: GenerateRequest,
    engine=Depends(_get_inference_engine),
) -> GenerateResponse | StreamingResponse:
    """Run inference. Set stream=true for SSE token streaming."""
    request = InferenceRequest(
        prompt=body.prompt,
        model_id=body.model_id,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        stream=body.stream,
        extra={"session_id": body.session_id} if body.session_id else {},
    )
    try:
        if body.stream:
            async def _event_stream():
                async for token in engine.stream(request):
                    yield f"data: {token}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(_event_stream(), media_type="text/event-stream")

        resp: InferenceResponse = await engine.run(request)
        return GenerateResponse(
            text=resp.text,
            model_id=resp.model_id,
            prompt_tokens=resp.prompt_tokens,
            completion_tokens=resp.completion_tokens,
            finish_reason=resp.finish_reason,
        )
    except ModelNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (InferenceError, ModelLoadError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/models/{model_id}/load", status_code=204)
async def load_model(model_id: str, engine=Depends(_get_inference_engine)) -> None:
    """Pre-load a model into memory."""
    try:
        await engine.load_model(model_id)
    except ModelNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ModelLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/models/{model_id}/unload", status_code=204)
async def unload_model(model_id: str, engine=Depends(_get_inference_engine)) -> None:
    """Release a model from memory."""
    try:
        await engine.unload_model(model_id)
    except ModelNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
