"""SSM-backed intent classifier using existing IInferencePort."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from backend.domain.ports.inference import IInferencePort, InferenceRequest

INTENT_SCHEMA = {
    "intent": "string",
    "confidence": "float 0..1",
    "entities": "object",
    "suggested_engine": "string",
}


@dataclass
class SSMIntentClassifier:
    inference: IInferencePort
    model_id: str | None = None
    max_tokens: int = 256
    temperature: float = 0.0

    PROMPT = (
        "You are an offline intent classifier for an enterprise AI platform. "
        "Return ONLY strict JSON with keys: intent, confidence, entities, suggested_engine. "
        "Possible intents: search_knowledge, question_answering, run_inference, list_models, "
        "load_model, ingest_document, delete_document, admin_action. "
        "Suggested engines: knowledge, inference, document, administration, knowledge+inference.\n\n"
        "Text: {text}\n"
        "Context: {context}\n"
        "JSON:"
    )

    async def classify(self, text: str, context: dict | None = None):
        response = await self.inference.run(
            InferenceRequest(
                prompt=self.PROMPT.format(text=text, context=json.dumps(context or {}, ensure_ascii=False)),
                model_id=self.model_id or "",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        )
        return self._parse_json(response.text)

    def _parse_json(self, raw: str) -> dict:
        raw = raw.strip()
        fenced = re.search(r"\{.*\}", raw, re.DOTALL)
        if fenced:
            raw = fenced.group(0)
        payload = json.loads(raw)
        return {
            "intent": str(payload.get("intent", "run_inference")),
            "confidence": float(payload.get("confidence", 0.5)),
            "entities": payload.get("entities", {}) or {},
            "suggested_engine": str(payload.get("suggested_engine", "inference")),
        }
