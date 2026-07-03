"""Unit tests — parsers."""
import json

from backend.infrastructure.document.parsers import (
    HTMLParser,
    JSONParser,
    PlainTextParser,
    detect_mime,
    get_parser,
)


def test_detect_mime_pdf():
    assert detect_mime("report.pdf") == "application/pdf"


def test_detect_mime_txt():
    assert detect_mime("notes.txt") == "text/plain"


def test_detect_mime_unknown():
    assert detect_mime("file.xyz") == "application/octet-stream"


def test_plain_text_parser_utf8():
    p = PlainTextParser()
    result = p.parse(b"Hello world", "file.txt")
    assert result.text == "Hello world"


def test_plain_text_parser_latin1():
    p = PlainTextParser()
    data = "Héllo".encode("latin-1")
    result = p.parse(data, "file.txt")
    assert "H" in result.text


def test_json_parser():
    p = JSONParser()
    data = json.dumps({"key": "value"}).encode()
    result = p.parse(data, "data.json")
    assert "key" in result.text


def test_html_parser_strips_scripts():
    p = HTMLParser()
    html = b"<html><head><script>alert(1)</script></head><body><p>Hello</p></body></html>"
    result = p.parse(html, "page.html")
    assert "Hello" in result.text
    assert "alert" not in result.text


def test_get_parser_pdf():
    p = get_parser("application/pdf")
    assert p is not None


def test_get_parser_unknown():
    assert get_parser("application/x-unknown-blob") is None
