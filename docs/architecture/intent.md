# Phase 4 — Intent Engine

## Overview

Phase 4 introduces a fully local **Intent Engine** that routes user requests to the proper engine using a hybrid strategy:

1. **Heuristic classification** — deterministic regex rules, entity extraction, zero dependencies.
2. **SSM refinement** — optional second-pass classification via the existing local Mamba inference engine.
3. **Knowledge peek** — optional top-1 semantic search to raise confidence for knowledge-oriented requests.

No network calls are performed at any stage.

## Integration points

- **Inference (Phase 1)**: `SSMIntentClassifier` uses the existing `IInferencePort` with a constrained JSON-only prompt.
- **Knowledge (Phase 3)**: `IntentService` optionally queries `IKnowledgePort` when the candidate intent is `search_knowledge` or `question_answering`.
- **API**: `/api/v1/intent/classify`

## Files

| File | Responsibility |
|---|---|
| `backend/domain/ports/intent.py` | Extended contracts: `IntentMode`, `IntentCandidate`, clarification fields |
| `backend/infrastructure/intent/rules.py` | Regex rules + entity extraction |
| `backend/infrastructure/intent/ssm_classifier.py` | Local SSM classifier via `IInferencePort` |
| `backend/infrastructure/intent/service.py` | Hybrid orchestration |
| `backend/infrastructure/intent/container.py` | DI factory |
| `backend/api/intent_router.py` | REST endpoint |
| `tests/unit/intent/*` | Rule, hybrid and JSON parsing tests |

## Supported intents

- `search_knowledge`
- `question_answering`
- `run_inference`
- `list_models`
- `load_model`
- `ingest_document`
- `delete_document`
- `admin_action`

## Clarification flow

If final confidence is below the configured threshold (default `0.55`), the engine sets:

- `needs_clarification = true`
- `clarification_question = "Richiesta ambigua. Confermi se vuoi: ...?"`

This allows ADMIN STUDIO or CLIENT to ask a disambiguation question before dispatching execution.

## Air-gap compliance

- Regex rules are pure Python.
- SSM classifier reuses the already local Mamba model.
- Knowledge peek uses the embedded ChromaDB collection from Phase 3.
- No cloud NLP, no remote classifier, no telemetry.
