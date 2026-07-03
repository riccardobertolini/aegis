"""Unit tests for DocumentEngine, ParserRegistry and Chunker."""
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def engine():
    from backend.infrastructure.adapters.document.document_engine import DocumentEngine
    return DocumentEngine(chunk_size=200, overlap=20, dedup=True)


# ------------------------------------------------------------------ #
# Parser tests                                                        #
# ------------------------------------------------------------------ #

def test_txt_parser(engine):
    doc, chunks = engine.ingest(FIXTURES / "sample.txt")
    assert doc.format.value == "txt"
    assert doc.word_count > 0
    assert len(chunks) >= 1


def test_md_parser(engine):
    doc, chunks = engine.ingest(FIXTURES / "sample.md")
    assert doc.format.value == "md"
    assert "Aegis" in doc.raw_text


def test_json_parser(engine):
    doc, chunks = engine.ingest(FIXTURES / "sample.json")
    assert doc.format.value == "json"
    assert "aegis" in doc.raw_text.lower()


def test_csv_parser(engine):
    doc, chunks = engine.ingest(FIXTURES / "sample.csv")
    assert doc.format.value == "csv"
    assert "Alice" in doc.raw_text


def test_xml_parser(engine):
    doc, chunks = engine.ingest(FIXTURES / "sample.xml")
    assert doc.format.value == "xml"
    assert "Aegis" in doc.raw_text


def test_html_parser(engine):
    doc, chunks = engine.ingest(FIXTURES / "sample.html")
    assert doc.format.value == "html"
    assert doc.title == "Aegis Sample HTML"


def test_email_parser(engine):
    doc, chunks = engine.ingest(FIXTURES / "sample.eml")
    assert doc.format.value == "email"
    assert "Alice" in doc.raw_text


# ------------------------------------------------------------------ #
# Chunker tests                                                       #
# ------------------------------------------------------------------ #

def test_chunker_dedup(engine):
    """Duplicate chunks must be removed when dedup=True."""
    doc, chunks = engine.ingest(FIXTURES / "sample.txt")
    hashes = [c.content_hash for c in chunks]
    assert len(hashes) == len(set(hashes)), "Duplicate chunks found"


def test_chunker_overlap():
    from backend.infrastructure.adapters.document.chunker import chunk_text
    from backend.infrastructure.adapters.document.models import DocumentFormat, ParsedDocument

    doc = ParsedDocument(
        source_path="/fake/test.txt",
        format=DocumentFormat.TXT,
        raw_text="A" * 600,
    )
    chunks = chunk_text(doc, chunk_size=200, overlap=50, dedup=False)
    assert len(chunks) >= 3
    # second chunk should start before end of first
    assert chunks[1].start_char < chunks[0].end_char


def test_unsupported_format_raises(engine):
    with pytest.raises(ValueError, match="No parser registered"):
        engine.ingest(Path("/tmp/test.unknownfmt"))


def test_missing_file_raises(engine):
    with pytest.raises(FileNotFoundError):
        engine.ingest(Path("/nonexistent/file.txt"))
