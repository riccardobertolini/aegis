# Aegis — Document & RAG Engine (Phase 3)

## Pipeline Overview

```
File Upload / Raw Bytes
    └─ DocumentParser        extract text (PDF/DOCX/TXT/MD/CSV)
    └─ TextChunker           sliding-window, sentence-boundary aware
    └─ LocalEmbedder         sentence-transformers (all-MiniLM-L6-v2 default)
    └─ ChromaKnowledgeAdapter ChromaDB embedded → cosine similarity index
    └─ DocumentModel (SQLite) metadata persistence

RAG Query
    └─ LocalEmbedder         embed query
    └─ ChromaKnowledgeAdapter top-k vector search
    └─ RAGService             context assembly + prompt augmentation
    └─ IInferencePort         SSM forward pass (Mamba)
    └─ RAGResponse            { answer, sources[], model_id, tokens }
```

## Why ChromaDB?

| Property | ChromaDB Embedded | FAISS | LanceDB |
|---|---|---|---|
| Server required | No | No | No |
| Persistence | Yes (local dir) | Manual | Yes |
| Metadata filtering | Yes | No | Yes |
| Air-gapped | Yes | Yes | Yes |
| Python native | Yes | C++ binding | Yes |
| Telemetry | Disabled (`anonymized_telemetry=False`) | N/A | N/A |

## Component Details

### DocumentParser
Formats supported out of the box:
- **PDF**: `pdfminer.six` — pure Python, no C dependencies
- **DOCX**: `python-docx`
- **TXT / MD / CSV / HTML**: direct UTF-8 decode
- **Fallback**: raw bytes → UTF-8 with error replacement

Detection order: magic bytes (PDF: `%PDF`, DOCX: `PK\x03\x04`) → file extension.

### TextChunker
Sliding-window algorithm with sentence-boundary detection:
- `chunk_size=512` chars (default)
- `chunk_overlap=64` chars — context continuity across chunks
- Hard-splits sentences longer than `chunk_size`
- Short fragments (< `min_chunk_len`) are dropped

### LocalEmbedder
Model: `all-MiniLM-L6-v2` (384 dim, ~22 MB, Apache-2.0 licence).

To pre-download for offline use (run once on an internet-connected machine):
```bash
python -m backend.infrastructure.rag.embedder all-MiniLM-L6-v2 --out models/embed
```
Then copy `models/embed/all-MiniLM-L6-v2/` to the air-gapped machine.

Environment variables set automatically:
```
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```
No automatic download ever happens.

### ChromaKnowledgeAdapter
- `PersistentClient` → data in `data/chroma/` (local directory)
- `anonymized_telemetry=False` → zero data egress
- One collection per knowledge base (configurable `collection_name`)
- Cosine similarity (`hnsw:space: cosine`)
- Metadata `where` filters forwarded to ChromaDB query

### RAGService
Prompt template:
```
You are Aegis, a helpful AI assistant.
Answer the user's question using ONLY the provided context.

=== CONTEXT ===
[1] <chunk 1 text>
[2] <chunk 2 text>
...
=== END CONTEXT ===

Question: <user query>

Answer:
```
Context truncated to `max_context_chars=4096` (configurable).

## API Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/documents/upload` | Upload + ingest file |
| `GET` | `/api/v1/documents` | List ingested documents |
| `DELETE` | `/api/v1/documents/{id}` | Delete doc + vectors |
| `POST` | `/api/v1/documents/search` | RAG query (retrieve + generate) |
| `POST` | `/api/v1/knowledge/ingest` | Ingest raw text docs |
| `GET` | `/api/v1/knowledge/documents` | List vector store docs |
| `DELETE` | `/api/v1/knowledge/documents/{id}` | Delete from vector store |
| `POST` | `/api/v1/knowledge/search` | Vector similarity search only |

## Adding a Custom Embed Model

1. Download model locally: `sentence-transformers` compatible
2. Place in `models/embed/<model-name>/`
3. Set `EMBED_MODEL=<model-name>` in `.env`
4. Restart Aegis

## Requirements

Add to `requirements/base.txt`:
```
pdfminer.six>=20221105
python-docx>=1.1
chromadb>=0.5
sentence-transformers>=3.0
```
