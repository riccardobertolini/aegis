"""Email (.eml) parser using stdlib email module."""
import email
import email.policy
from pathlib import Path

from ..models import DocumentFormat, ParsedDocument
from .base import BaseParser


class EmailParser(BaseParser):
    supported_formats = [DocumentFormat.EMAIL]

    def parse(self, path: Path) -> ParsedDocument:
        try:
            raw = path.read_bytes()
            msg = email.message_from_bytes(raw, policy=email.policy.default)
            subject = str(msg.get("subject", ""))
            from_ = str(msg.get("from", ""))
            date_ = str(msg.get("date", ""))
            parts: list[str] = [f"Subject: {subject}", f"From: {from_}", f"Date: {date_}", ""]
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            parts.append(payload.decode("utf-8", errors="replace"))
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode("utf-8", errors="replace"))
            raw_text = "\n".join(parts)
            metadata: dict = {"from": from_, "subject": subject, "date": date_}
        except Exception as exc:  # noqa: BLE001
            raw_text = f"[Email parse error: {exc}]"
            metadata = {}

        return ParsedDocument(
            source_path=str(path),
            format=DocumentFormat.EMAIL,
            title=path.stem,
            raw_text=raw_text,
            metadata=metadata,
        )
