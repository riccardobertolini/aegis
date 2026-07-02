"""Aegis — FastAPI application factory.

Startup sequence:
    1. Load settings (pydantic-settings, .env)
    2. Initialise DB (create tables, run Alembic migrations)
    3. Build InferenceContainer (scan models/, lazy-load)
    4. Register all routers
    5. Serve via Uvicorn
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from backend.shared.config import get_settings
from backend.shared.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)

    # --- DB init ---
    try:
        from backend.infrastructure.database.engine import create_all_tables
        await create_all_tables()
        logger.info("Database tables ready")
    except Exception as exc:
        logger.error("DB init failed: %s", exc)

    # --- Inference container ---
    models_root = Path(settings.base_dir) / "models" if hasattr(settings, "base_dir") else Path("models")
    try:
        from backend.infrastructure.inference.container import InferenceContainer
        container = InferenceContainer.build(
            models_root=models_root,
            default_model_id=getattr(settings, "default_model_id", ""),
            system_prompt=getattr(
                settings,
                "system_prompt",
                "You are Aegis, a helpful AI assistant running fully offline.",
            ),
        )
        app.state.inference_container = container
        logger.info("InferenceContainer ready — models: %s", container.loader.list_available())
    except Exception as exc:
        logger.error("InferenceContainer init failed: %s", exc)
        app.state.inference_container = None

    yield
    # --- Shutdown ---
    logger.info("Aegis shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Aegis AI Platform",
        description="Enterprise offline-first AI platform (SSM/Mamba)",
        version="0.6.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    from backend.api.routers import register_routers
    register_routers(app)

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "version": "0.6.0"}

    return app


app = create_app()
