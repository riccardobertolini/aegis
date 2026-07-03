"""Unit tests for DocumentParser."""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.infrastructure.rag.parser import DocumentParser


@pytest.fixture
def parser() -> DocumentParser:
    return DocumentParser(max_file_bytes=10 * 1024 * 1024)


def test_parse_txt_bytes(parser: DocumentParser):
    data = b"Hello world.\nThis is a test document.\n\nSecond paragraph here."
    doc = parser.parse_bytes(data, "test.txt")
    assert doc.filename == "test.txt"
    assert doc.mime_type == "text/plain"
    assert len(doc.chunks) >= 1
    assert "Hello world" in " ".join(doc.chunks)


def test_parse_md_bytes(parser: DocumentParser):
    data = b"# Title\n\nSome markdown content.\n\nAnother section."
    doc = parser.parse_bytes(data, "readme.md")
    assert doc.mime_type == "text/markdown"
    assert len(doc.chunks) >= 1


def test_parse_csv_bytes(parser: DocumentParser):
    data = b"name,age\nAlice,30\nBob,25\n"
    doc = parser.parse_bytes(data, "data.csv")
    assert doc.mime_type == "text/csv"
    assert doc.id.startswith("doc_")


def test_parse_file_txt(parser: DocumentParser, tmp_path: Path):
    f = tmp_path / "sample.txt"
    f.write_text("Line one.\n\nLine two.", encoding="utf-8")
    doc = parser.parse_file(f)
    assert doc.filename == "sample.txt"
    assert len(doc.chunks) >= 1


def test_parse_exceeds_max_size(parser: DocumentParser):
    big = b"x" * (11 * 1024 * 1024)  # 11 MB
    with pytest.raises(ValueError, match="exceeds max size"):
        parser.parse_bytes(big, "huge.txt")


def test_parse_checksum_in_metadata(parser: DocumentParser):
    data = b"checksum test"
    doc = parser.parse_bytes(data, "check.txt")
    assert "checksum_sha256" in doc.metadata
    assert len(doc.metadata["checksum_sha256"]) == 64


def test_parse_id_deterministic(parser: DocumentParser):
    data = b"same content"
    doc1 = parser.parse_bytes(data, "file.txt")
    doc2 = parser.parse_bytes(data, "file.txt")
    assert doc1.id == doc2.id


def test_parse_id_differs_by_filename(parser: DocumentParser):
    data = b"same content"
    doc1 = parser.parse_bytes(data, "a.txt")
    doc2 = parser.parse_bytes(data, "b.txt")
    assert doc1.id != doc2.id
