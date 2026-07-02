"""Router package — registers all API routers."""
from fastapi import FastAPI

from .documents import router as documents_router
from .knowledge import router as knowledge_router
from .intent import router as intent_router


def register_routers(app: FastAPI) -> None:
    """Attach all routers to the FastAPI application."""
    app.include_router(documents_router)
    app.include_router(knowledge_router)
    app.include_router(intent_router)
