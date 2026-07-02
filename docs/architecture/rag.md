# Phase 3 — Document + RAG Engine

## Overview

Phase 3 implements the full **Retrieve-Augment-Generate** pipeline, connecting the local document corpus to the Mamba SSM inference engine from Phase 1.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Document + RAG Engine                    │
│                                                                 │
│  Upload/ingest                                                  │
│  ───────────►  Parser (PDF/DOCX/XLSX/HTML/JSON/text)            │
│               ──────────►  TextChunker (recursive split)        │
│                            ──────────►  Embedder (local ST)     │
│                                         ──────────►  ChromaDB  │
│                                                     (vectors)  │
│                                                     SQLite      │
│                                                     (metadata) │
│                                                                 │
│  RAG Query                                                      │
│  ──────────►  Embed question  ──►  ChromaDB (top-k retrieval)  │
│                                    ──────────►  Build prompt    │
│                                                ──────────►      │
│                                                Mamba SSM        │
│                                                (generate)       │
│                                                   ──────────►  │
│                                                   Answer +      │
│                                                   Sources       │
└─────────────────────────────────────────────────────────────────┘
```

## Components

| File | Responsibility |
|---|---|
| `parsers.py` | Format-specific text extraction (PDF, DOCX, XLSX, HTML, JSON, plain text) |
| `chunker.py` | Recursive character splitter with configurable size + overlap |
| `embedder.py` | `SentenceTransformerEmbedder` (local) + `FallbackHashEmbedder` (no-ML CI) |
| `vector_store.py` | ChromaDB embedded persistent store, cosine similarity |
| `db_store.py` | SQLite/SQLModel metadata store (async) |
| `document_service.py` | `IDocumentPort` implementation — orchestrates ingest pipeline |
| `knowledge_service.py` | `IKnowledgePort` implementation — semantic search |
| `rag_pipeline.py` | RAG orchestrator: retrieve → augment → generate (streaming + batch) |
| `container.py` | DI factory: `build_document_container()` |

## REST API (`/api/v1/documents`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/upload` | Upload + ingest a file |
| `GET` | `/` | List all documents (paginated) |
| `GET` | `/{id}` | Get document by ID |
| `DELETE` | `/{id}` | Delete document (DB + vectors) |
| `POST` | `/search` | Semantic search (embedding-based) |
| `POST` | `/rag/query` | RAG answer (batch) |
| `POST` | `/rag/stream` | RAG answer (SSE streaming) |

## Supported Formats

| Format | Parser | Notes |
|---|---|---|
| `.pdf` | pdfminer.six | Pure Python, no binary deps |
| `.docx` | python-docx | Extracts paragraphs |
| `.xlsx` | openpyxl | All sheets, tab-separated |
| `.html` | stdlib HTMLParser | Strips scripts/styles |
| `.json` | stdlib json | Pretty-prints for readability |
| `.txt/.md/.rst/.csv` | PlainTextParser | UTF-8/Latin-1/CP1252 |
| `.py/.js/.ts/.go/.rs` | PlainTextParser | Source code |

## Embedding Models (Offline)

Copy a sentence-transformers model to `models/embeddings/<name>/` before first run:

```bash
# Example: all-MiniLM-L6-v2 (22 MB, 384 dims)
cp -r /media/usb/all-MiniLM-L6-v2 ./models/embeddings/
```

Set in `.env`:
```
EMBEDDING_MODEL_PATH=./models/embeddings/all-MiniLM-L6-v2
```

If no model is configured, the `FallbackHashEmbedder` is used automatically (for development/CI; not suitable for production retrieval quality).

## Air-Gap Compliance

- `SentenceTransformer(..., local_files_only=True)` — prevents any HTTP call
- ChromaDB in `PersistentClient` mode — no external server
- All document data stays in `data/chroma/` and `data/aegis.db`
- No telemetry, no analytics, no network access
