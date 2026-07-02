"""Format parsers."""
from .base import BaseParser
from .pdf_parser import PdfParser
from .docx_parser import DocxParser
from .xlsx_parser import XlsxParser
from .pptx_parser import PptxParser
from .text_parser import TextParser
from .html_parser import HtmlParser
from .csv_parser import CsvParser
from .json_parser import JsonParser
from .xml_parser import XmlParser
from .email_parser import EmailParser

__all__ = [
    "BaseParser",
    "PdfParser",
    "DocxParser",
    "XlsxParser",
    "PptxParser",
    "TextParser",
    "HtmlParser",
    "CsvParser",
    "JsonParser",
    "XmlParser",
    "EmailParser",
]
