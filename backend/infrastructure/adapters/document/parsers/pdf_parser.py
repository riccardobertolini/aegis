"""PDF parser using pdfminer.six (offline, no cloud)."""
from pathlib import Path

from ..models import DocumentFormat, ParsedDocument
from .base import BaseParser


class PdfParser(BaseParser):
    supported_formats = [DocumentFormat.PDF]

    def parse(self, path: Path) -> ParsedDocument:
        try:
            from pdfminer.high_level import extract_text
            from pdfminer.pdfpage import PDFPage

            raw_text = extract_text(str(path))
            with open(path, "rb") as fh:
                pages = list(PDFPage.get_pages(fh))
            page_count = len(pages)
        except ImportError:
            raw_text = f"[pdfminer.six not installed — cannot parse {path.name}]"
            page_count = 0
        except Exception as exc:  # noqa: BLE001
            raw_text = f"[PDF parse error: {exc}]"
            page_count = 0

        return ParsedDocument(
            source_path=str(path),
            format=DocumentFormat.PDF,
            title=path.stem,
            raw_text=raw_text,
            page_count=page_count,
            metadata={"file_size": path.stat().st_size},
        )
