"""Aegis — FastAPI application factory.

Startup sequence:
    1. Load settings + configure logging
    2. DB: create all tables
    3. InferenceContainer: scan models/, lazy-load
    4. DocumentContainer: parser + chunker + embedder + chroma + RAG
    5. TrainingContainer: dataset manager + trainer + experiment tracker
    6. Register routers
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from backend.shared.config import get_settings
from backend.shared.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)

    base_dir = Path(getattr(settings, "base_dir", "."))
    models_root = base_dir / "models"
    data_dir = base_dir / "data"
    experiments_root = base_dir / "experiments"
    datasets_root = base_dir / "datasets"
    data_dir.mkdir(parents=True, exist_ok=True)
    experiments_root.mkdir(parents=True, exist_ok=True)
    datasets_root.mkdir(parents=True, exist_ok=True)

    # --- DB ---
    try:
        from backend.infrastructure.database.engine import create_all_tables
        await create_all_tables()
        logger.info("Database tables ready")
    except Exception as exc:
        logger.error("DB init failed: %s", exc)

    # --- Inference ---
    inference_container = None
    try:
        from backend.infrastructure.inference.container import InferenceContainer
        inference_container = InferenceContainer.build(
            models_root=models_root,
            default_model_id=getattr(settings, "default_model_id", ""),
            system_prompt=getattr(
                settings, "system_prompt",
                "You are Aegis, a helpful AI assistant running fully offline.",
            ),
        )
        app.state.inference_container = inference_container
        logger.info("InferenceContainer ready — models: %s", inference_container.loader.list_available())
    except Exception as exc:
        logger.error("InferenceContainer init failed: %s", exc)
        app.state.inference_container = None

    # --- Document / RAG ---
    try:
        from backend.infrastructure.rag.container import DocumentContainer
        embed_model = getattr(settings, "embed_model", "all-MiniLM-L6-v2")
        doc_container = DocumentContainer.build(
            data_dir=data_dir,
            inference=inference_container.inference if inference_container else _NullInference(),
            models_root=models_root,
            embed_model=embed_model,
            default_model_id=getattr(settings, "default_model_id", ""),
        )
        app.state.document_container = doc_container
        logger.info("DocumentContainer ready (chroma=%s/chroma)", data_dir)
    except Exception as exc:
        logger.error("DocumentContainer init failed: %s", exc)
        app.state.document_container = None

    # --- Training ---
    try:
        from backend.infrastructure.training.container import build_training_container
        loader = inference_container.loader if inference_container else None
        training_container = build_training_container(
            models_root=models_root,
            experiments_root=experiments_root,
            datasets_root=datasets_root,
            model_loader=loader,
        )
        app.state.training_container = training_container
        logger.info("TrainingContainer ready (datasets=%s, experiments=%s)", datasets_root, experiments_root)
    except Exception as exc:
        logger.error("TrainingContainer init failed: %s", exc)
        app.state.training_container = None

    yield
    logger.info("Aegis shutting down")


class _NullInference:
    """Placeholder inference port when no model is loaded."""
    async def run(self, request):
        from backend.domain.ports.inference import InferenceResponse
        return InferenceResponse(
            text="[No model loaded. Please load a model first.]",
            model_id="none",
            prompt_tokens=0,
            completion_tokens=0,
            finish_reason="error",
        )
    async def stream(self, request):
        yield "[No model loaded.]"
    async def list_models(self):
        return []
    async def load_model(self, model_id):
        pass
    async def unload_model(self, model_id):
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="Aegis AI Platform",
        description="Enterprise offline-first AI platform (SSM/Mamba)",
        version="0.8.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    from backend.api.routers import register_routers
    register_routers(app)

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "version": "0.8.0"}

    return app


app = create_app()
