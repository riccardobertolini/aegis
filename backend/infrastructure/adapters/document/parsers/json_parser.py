"""JSON parser using stdlib json."""
import json
from pathlib import Path

from ..models import DocumentFormat, ParsedDocument
from .base import BaseParser


def _flatten(obj: object, prefix: str = "") -> list[str]:
    lines: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            lines.extend(_flatten(v, f"{prefix}{k}: "))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            lines.extend(_flatten(v, f"{prefix}[{i}] "))
    else:
        lines.append(f"{prefix}{obj}")
    return lines


class JsonParser(BaseParser):
    supported_formats = [DocumentFormat.JSON]

    def parse(self, path: Path) -> ParsedDocument:
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            raw_text = "\n".join(_flatten(data))
            metadata: dict = {"top_keys": list(data.keys()) if isinstance(data, dict) else []}
        except Exception as exc:  # noqa: BLE001
            raw_text = f"[JSON parse error: {exc}]"
            metadata = {}

        return ParsedDocument(
            source_path=str(path),
            format=DocumentFormat.JSON,
            title=path.stem,
            raw_text=raw_text,
            metadata=metadata,
        )
