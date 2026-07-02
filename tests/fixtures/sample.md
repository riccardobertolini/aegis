# Sample Markdown Document

## Introduction

This is a **Markdown** fixture for testing the `MarkdownParser` in Aegis.

## Features

- Offline-first
- Air-gapped
- SSM-only (no Transformers)

## Code Sample

```python
from backend.infrastructure.adapters.document import DocumentEngine
engine = DocumentEngine()
doc, chunks = engine.ingest("sample.md")
```
