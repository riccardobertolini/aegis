"""Central router registry."""
from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    from backend.api.routers.inference import router as inference_router
    from backend.api.routers.document import router as document_router
    from backend.api.routers.intent import router as intent_router
    from backend.api.memory_router import router as memory_router
    from backend.api.training_router import router as training_router
    from backend.api.admin_router import router as admin_router

    app.include_router(inference_router)
    app.include_router(document_router)
    app.include_router(intent_router)
    app.include_router(memory_router)
    app.include_router(training_router)
    app.include_router(admin_router)
