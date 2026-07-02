"""CSV parser using stdlib csv module."""
import csv
import io
from pathlib import Path

from ..models import DocumentFormat, ParsedDocument
from .base import BaseParser


class CsvParser(BaseParser):
    supported_formats = [DocumentFormat.CSV]

    def parse(self, path: Path) -> ParsedDocument:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            reader = csv.reader(io.StringIO(raw))
            rows = list(reader)
            raw_text = "\n".join("\t".join(row) for row in rows)
            metadata: dict = {"row_count": len(rows), "col_count": len(rows[0]) if rows else 0}
        except Exception as exc:  # noqa: BLE001
            raw_text = f"[CSV parse error: {exc}]"
            metadata = {}

        return ParsedDocument(
            source_path=str(path),
            format=DocumentFormat.CSV,
            title=path.stem,
            raw_text=raw_text,
            metadata=metadata,
        )
