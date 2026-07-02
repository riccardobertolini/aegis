# FASE 4 — Intent Engine + Modalità Operative

## Panoramica

```
User text
    │
    ▼
[IntentClassifier]  ←── TF-IDF + cosine similarity (pure Python, offline)
    │  IntentPrediction (intent, confidence, ambiguous, fallback)
    ▼
[ModeRouter]  ←── feature flags per-intent (abilitabile/disabilitabile)
    │
    ├─ CLASSIFICATION    → ClassificationModality
    ├─ DOCUMENT_ANALYSIS → DocumentAnalysisModality
    ├─ EXTRACTION        → ExtractionModality
    ├─ NER               → NerModality
    ├─ SUMMARY           → SummaryModality
    ├─ TRANSLATION       → TranslationModality
    ├─ REWRITE           → RewriteModality
    ├─ QA                → QaModality
    ├─ RAG               → RagModality  (usa KnowledgeEngine FASE 3)
    ├─ CONVERSATION      → ConversationModality
    ├─ TIMESERIES        → TimeseriesModality
    ├─ LOG_ANALYSIS      → LogAnalysisModality
    ├─ SPEECH            → SpeechModality  (delega a ISpeechPort)
    └─ UNKNOWN           → fallback → CONVERSATION
    │
    ▼
[ModalityResponse]  →  API / Client
```

## Componenti

### IntentClassifier

- Algoritmo: TF-IDF + cosine similarity, pure Python, zero dipendenze ML
- Corpus seed: 13 intent × ~8 frasi campione
- Estendibile a runtime via `add_examples(intent, phrases)`
- Threshold configurabile (default 0.05); sotto soglia → UNKNOWN + fallback
- Ambiguity detection: se delta tra primo e secondo candidato < margin (0.02)

### ModeRouter

- Feature flags per intent: `enable(intent)` / `disable(intent)`
- Intent disabilitato → fallback automatico a CONVERSATION
- Modality registry: dict `IntentLabel → BaseModality`
- Ogni modality è indipendente e sostituibile (Open/Closed principle)

### Contratti comuni

| Modello | Campi chiave |
|---|---|
| `ModalityRequest` | session_id, intent, text, documents, kb_ids, parameters, context |
| `ModalityResponse` | session_id, intent, result, confidence, citations, fallback_used, error |

### RAG Modality

Collega FASE 3 (KnowledgeEngine) con FASE 4: se `kb_ids` è presente
e `KnowledgeEngine` è iniettato, esegue il retrieval vettoriale prima
di costruire il prompt per CoreAI. Degrada gracefully se KB vuota.

## API REST

| Metodo | Path | Descrizione |
|---|---|---|
| POST | `/intent/classify` | Classifica testo → restituisce intent + confidence |
| GET | `/intent/intents` | Lista tutti gli intent supportati |

## Vincoli rispettati

- ✅ Classificatore completamente offline (TF-IDF puro, nessun modello esterno)
- ✅ Feature flags: ogni modalità abilitabile/disabilitabile via config
- ✅ Contratti comuni `ModalityRequest` / `ModalityResponse`
- ✅ Fallback su UNKNOWN e su modality disabilitata
- ✅ Ogni modality è un modulo indipendente (BaseModality ABC)
- ✅ RAG modality integra KnowledgeEngine dalla FASE 3
- ✅ Speech modality delegata a ISpeechPort (implementazione futura)
