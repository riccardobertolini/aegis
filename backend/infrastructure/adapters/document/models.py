"""Domain models for the Document Engine."""
from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    TXT = "txt"
    MARKDOWN = "md"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    EMAIL = "email"
    UNKNOWN = "unknown"


FORMAT_EXTENSIONS: dict[str, DocumentFormat] = {
    ".pdf": DocumentFormat.PDF,
    ".docx": DocumentFormat.DOCX,
    ".doc": DocumentFormat.DOCX,
    ".xlsx": DocumentFormat.XLSX,
    ".xls": DocumentFormat.XLSX,
    ".pptx": DocumentFormat.PPTX,
    ".ppt": DocumentFormat.PPTX,
    ".txt": DocumentFormat.TXT,
    ".md": DocumentFormat.MARKDOWN,
    ".markdown": DocumentFormat.MARKDOWN,
    ".html": DocumentFormat.HTML,
    ".htm": DocumentFormat.HTML,
    ".csv": DocumentFormat.CSV,
    ".json": DocumentFormat.JSON,
    ".xml": DocumentFormat.XML,
    ".eml": DocumentFormat.EMAIL,
    ".msg": DocumentFormat.EMAIL,
}


def detect_format(path: Path) -> DocumentFormat:
    return FORMAT_EXTENSIONS.get(path.suffix.lower(), DocumentFormat.UNKNOWN)


class ParsedDocument(BaseModel):
    """Result of parsing a document file."""

    source_path: str
    format: DocumentFormat
    title: str = ""
    author: str = ""
    created_at: datetime | None = None
    modified_at: datetime | None = None
    language: str = "unknown"
    page_count: int = 0
    word_count: int = 0
    raw_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.raw_text.encode()).hexdigest()
        if not self.word_count:
            self.word_count = len(self.raw_text.split())


class TextChunk(BaseModel):
    """A chunk of text ready for embedding."""

    chunk_id: str
    document_id: str
    source_path: str
    text: str
    chunk_index: int
    total_chunks: int
    start_char: int
    end_char: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.text.encode()).hexdigest()
