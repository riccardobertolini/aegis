"""Unit tests for SSM-backed intent classifier."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.infrastructure.intent.ssm_classifier import SSMIntentClassifier


@pytest.mark.asyncio
async def test_ssm_classifier_parses_json_response():
    inference = AsyncMock()
    inference.run.return_value = MagicMock(
        text=json.dumps(
            {
                "intent": "search_knowledge",
                "confidence": 0.92,
                "entities": {"top_k": 5},
                "suggested_engine": "knowledge",
            }
        )
    )
    classifier = SSMIntentClassifier(inference=inference, model_id="intent-model")
    result = await classifier.classify("cerca nel manuale")
    assert result["intent"] == "search_knowledge"
    assert result["confidence"] == 0.92
    assert result["entities"]["top_k"] == 5
    assert result["suggested_engine"] == "knowledge"


@pytest.mark.asyncio
async def test_ssm_classifier_extracts_json_from_fenced_text():
    inference = AsyncMock()
    inference.run.return_value = MagicMock(
        text='```json\n{"intent":"run_inference","confidence":0.7,"entities":{},"suggested_engine":"inference"}\n```'
    )
    classifier = SSMIntentClassifier(inference=inference, model_id="intent-model")
    result = await classifier.classify("genera testo")
    assert result["intent"] == "run_inference"
