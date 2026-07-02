# FASE 3 — Document Engine & Knowledge Engine (RAG locale)

## Panoramica

Questa fase implementa l'intera pipeline di ingestion documentale e il motore RAG, 
entrambi **100% offline** e **air-gapped**.

```
File su disco
    │
    ▼
[ParserRegistry]
    │  PDF / DOCX / XLSX / PPTX / TXT / MD / HTML / CSV / JSON / XML / EML
    ▼
[ParsedDocument]  ←── testo + metadati estratti
    │
    ▼
[Chunker]  ←── chunk sovrapposti, deduplicazione per hash
    │
    ▼
[EmbeddingEngine]  ←── sentence-transformers locale, local_files_only=True
    │
    ▼
[ChromaVectorStore]  ←── PersistentClient, una collection per KB
    │
    ▼
Query utente → embed → vector search → rank → [RagContext] → Inference Engine
```

## Componenti

### Document Engine (`infrastructure/adapters/document/`)

| File | Responsabilità |
|---|---|
| `models.py` | `ParsedDocument`, `TextChunk`, `DocumentFormat`, `detect_format()` |
| `parsers/base.py` | `BaseParser` ABC |
| `parsers/*.py` | Parser per ogni formato |
| `parser_registry.py` | Risoluzione parser per estensione |
| `chunker.py` | Chunking con overlap + deduplicazione |
| `document_engine.py` | `DocumentEngine` → implementa `IDocumentPort` |

### Knowledge Engine (`infrastructure/adapters/knowledge/`)

| File | Responsabilità |
|---|---|
| `models.py` | `KnowledgeBase`, `RetrievedChunk`, `RagContext` |
| `embedding_engine.py` | `EmbeddingEngine` — sentence-transformers offline |
| `vector_store.py` | `ChromaVectorStore` — ChromaDB embedded |
| `knowledge_engine.py` | `KnowledgeEngine` → implementa `IKnowledgePort` |

## Modello di embedding

Il modello **non viene mai scaricato automaticamente**. Procedura air-gapped:

```bash
# Su macchina con accesso internet:
pip install sentence-transformers
python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('all-MiniLM-L6-v2').save('tmp_model')
"
# Copiare tmp_model/ → models/embeddings/all-MiniLM-L6-v2/
# sulla macchina air-gapped
```

Impostare nel `.env`:
```
AEGIS_EMBEDDING_MODEL_DIR=models/embeddings/all-MiniLM-L6-v2
```

## API REST

| Metodo | Path | Descrizione |
|---|---|---|
| POST | `/documents/ingest` | Parsa e chunka un file |
| GET | `/documents/formats` | Lista formati supportati |
| POST | `/knowledge/kb` | Crea una Knowledge Base |
| GET | `/knowledge/kb` | Lista KB (filtri: category, assistant_id) |
| DELETE | `/knowledge/kb/{id}` | Elimina KB e indice |
| POST | `/knowledge/document` | Indicizza documento in una KB |
| POST | `/knowledge/retrieve` | RAG: retrieval + contesto |
| GET | `/knowledge/kb/{id}/integrity` | Verifica integrità indice |

## Vincoli rispettati

- ✅ Nessun download automatico di modelli
- ✅ Nessuna chiamata HTTP esterna
- ✅ ChromaDB `PersistentClient` — embedded, nessun server
- ✅ `local_files_only=True` in sentence-transformers
- ✅ Separazione dominio/infrastruttura/interfaccia (Ports & Adapters)
- ✅ Ogni KB ha una collection Chroma isolata
