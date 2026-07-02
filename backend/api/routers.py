"""Central router registry."""
from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    from backend.api.inference_router import router as inference_router
    from backend.api.document_router import router as document_router

    app.include_router(inference_router)
    app.include_router(document_router)
