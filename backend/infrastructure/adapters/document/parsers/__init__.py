"""Format parsers."""
from .base import BaseParser
from .csv_parser import CsvParser
from .docx_parser import DocxParser
from .email_parser import EmailParser
from .html_parser import HtmlParser
from .json_parser import JsonParser
from .pdf_parser import PdfParser
from .pptx_parser import PptxParser
from .text_parser import TextParser
from .xlsx_parser import XlsxParser
from .xml_parser import XmlParser

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
