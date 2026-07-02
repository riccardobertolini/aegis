"""XML parser using stdlib xml.etree."""
import xml.etree.ElementTree as ET
from pathlib import Path

from ..models import DocumentFormat, ParsedDocument
from .base import BaseParser


def _iter_text(element: ET.Element) -> list[str]:
    parts: list[str] = []
    if element.text and element.text.strip():
        parts.append(f"{element.tag}: {element.text.strip()}")
    for child in element:
        parts.extend(_iter_text(child))
    return parts


class XmlParser(BaseParser):
    supported_formats = [DocumentFormat.XML]

    def parse(self, path: Path) -> ParsedDocument:
        try:
            tree = ET.parse(str(path))
            root = tree.getroot()
            raw_text = "\n".join(_iter_text(root))
            metadata: dict = {"root_tag": root.tag}
        except Exception as exc:  # noqa: BLE001
            raw_text = f"[XML parse error: {exc}]"
            metadata = {}

        return ParsedDocument(
            source_path=str(path),
            format=DocumentFormat.XML,
            title=path.stem,
            raw_text=raw_text,
            metadata=metadata,
        )
