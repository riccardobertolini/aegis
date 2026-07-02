"""Application entry point."""
from fastapi import FastAPI

from backend.api.routers import register_routers
from backend.shared.config import get_settings
from backend.shared.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="Aegis",
        version="0.1.0",
        description="Offline-First Enterprise AI Platform",
        # Disable automatic docs in production (air-gapped)
        docs_url="/docs" if settings.aegis_env == "development" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.aegis_env == "development" else None,
    )

    register_routers(app)
    return app


app = create_app()
