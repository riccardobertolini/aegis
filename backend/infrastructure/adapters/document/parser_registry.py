"""Registry that maps DocumentFormat → BaseParser."""
from pathlib import Path

from .models import DocumentFormat, ParsedDocument, detect_format
from .parsers import (
    BaseParser,
    CsvParser,
    DocxParser,
    EmailParser,
    HtmlParser,
    JsonParser,
    PdfParser,
    PptxParser,
    TextParser,
    XlsxParser,
    XmlParser,
)


class ParserRegistry:
    """Resolves the right parser for a given file path."""

    def __init__(self) -> None:
        self._parsers: dict[DocumentFormat, BaseParser] = {}
        for parser in [
            PdfParser(),
            DocxParser(),
            XlsxParser(),
            PptxParser(),
            TextParser(),
            HtmlParser(),
            CsvParser(),
            JsonParser(),
            XmlParser(),
            EmailParser(),
        ]:
            for fmt in parser.supported_formats:
                self._parsers[fmt] = parser

    def parse(self, path: Path) -> ParsedDocument:
        fmt = detect_format(path)
        parser = self._parsers.get(fmt)
        if parser is None:
            raise ValueError(f"No parser registered for format: {fmt} ({path.suffix})")
        return parser.parse(path)

    def supports(self, path: Path) -> bool:
        return detect_format(path) in self._parsers
