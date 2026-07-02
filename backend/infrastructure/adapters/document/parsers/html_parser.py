"""HTML parser using BeautifulSoup4 (offline)."""
from pathlib import Path

from ..models import DocumentFormat, ParsedDocument
from .base import BaseParser


class HtmlParser(BaseParser):
    supported_formats = [DocumentFormat.HTML]

    def parse(self, path: Path) -> ParsedDocument:
        raw_html = path.read_text(encoding="utf-8", errors="replace")
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(raw_html, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else path.stem
            for tag in soup(["script", "style", "head"]):
                tag.decompose()
            raw_text = soup.get_text(separator="\n", strip=True)
        except ImportError:
            title = path.stem
            raw_text = raw_html
        except Exception as exc:  # noqa: BLE001
            title = path.stem
            raw_text = f"[HTML parse error: {exc}]"

        return ParsedDocument(
            source_path=str(path),
            format=DocumentFormat.HTML,
            title=title,
            raw_text=raw_text,
        )
