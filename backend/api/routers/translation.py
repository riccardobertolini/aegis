"""API router — Translation Engine."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.domain.ports.translation import TranslationRequest
from backend.infrastructure.adapters.translation import TranslationEngine
from backend.shared.config import get_settings

router = APIRouter(prefix="/translate", tags=["translation"])


def _engine() -> TranslationEngine:
    return TranslationEngine(settings=get_settings())


class TranslateBody(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str


@router.post("/")
async def translate(
    body: TranslateBody,
    engine: TranslationEngine = Depends(_engine),
):
    req = TranslationRequest(
        text=body.text,
        source_lang=body.source_lang,
        target_lang=body.target_lang,
    )
    result = await engine.translate(req)
    return {
        "translated": result.translated_text,
        "source_lang": result.source_lang,
        "target_lang": result.target_lang,
        "confidence": result.confidence,
    }


@router.get("/pairs")
async def list_pairs(engine: TranslationEngine = Depends(_engine)):
    pairs = await engine.list_language_pairs()
    return {"pairs": [{"src": s, "tgt": t} for s, t in pairs]}


@router.post("/detect")
async def detect_language(body: dict):
    from backend.infrastructure.adapters.translation.lang_detect import detect_language as _detect
    text = body.get("text", "")
    lang, confidence = _detect(text)
    return {"language": lang, "confidence": confidence}
