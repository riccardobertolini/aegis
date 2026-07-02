"""API router registry."""
from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    from backend.api.routers.intent import router as intent_router
    from backend.api.routers.memory import router as memory_router
    from backend.api.routers.translation import router as translation_router
    from backend.api.routers.timeseries import router as timeseries_router
    from backend.api.routers.logs import router as logs_router

    app.include_router(intent_router)
    app.include_router(memory_router)
    app.include_router(translation_router)
    app.include_router(timeseries_router)
    app.include_router(logs_router)
