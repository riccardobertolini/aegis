"""Abstract base for all format parsers."""
from abc import ABC, abstractmethod
from pathlib import Path

from ..models import DocumentFormat, ParsedDocument


class BaseParser(ABC):
    """Every parser must implement this contract."""

    @property
    @abstractmethod
    def supported_formats(self) -> list[DocumentFormat]:
        ...

    @abstractmethod
    def parse(self, path: Path) -> ParsedDocument:
        """Parse file at *path* and return a ParsedDocument."""
        ...

    def can_handle(self, fmt: DocumentFormat) -> bool:
        return fmt in self.supported_formats
