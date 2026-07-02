"""Central router registry."""
from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    from backend.api.inference_router import router as inference_router
    app.include_router(inference_router, prefix="/api/v1/inference", tags=["inference"])

    from backend.api.document_router import doc_router, knowledge_router
    app.include_router(doc_router, prefix="/api/v1/documents", tags=["documents"])
    app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["knowledge"])

    try:
        from backend.api.security_router import router as security_router  # type: ignore
        app.include_router(security_router, prefix="/api/v1/security", tags=["security"])
    except ImportError:
        pass
