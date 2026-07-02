"""Plain text and Markdown parser."""
from pathlib import Path

from ..models import DocumentFormat, ParsedDocument
from .base import BaseParser


class TextParser(BaseParser):
    supported_formats = [DocumentFormat.TXT, DocumentFormat.MARKDOWN]

    def parse(self, path: Path) -> ParsedDocument:
        try:
            raw_text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            raw_text = f"[Text read error: {exc}]"

        fmt = DocumentFormat.MARKDOWN if path.suffix.lower() in (".md", ".markdown") else DocumentFormat.TXT
        return ParsedDocument(
            source_path=str(path),
            format=fmt,
            title=path.stem,
            raw_text=raw_text,
            metadata={"encoding": "utf-8"},
        )
