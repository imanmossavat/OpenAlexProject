from typing import Dict, Type

from .extractors.base import BaseExtractor
from .extractors import (
    PdfExtractor,
    DocxExtractor,
    HtmlExtractor,
    XmlExtractor,
    LatexExtractor,
)


class ExtractorFactory:
    """Factory responsible for returning extractor instances."""

    def __init__(self) -> None:
        self._creators: Dict[str, Type[BaseExtractor]] = {
            # PDF
            "application/pdf": PdfExtractor,
            # DOCX
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxExtractor,
            # HTML
            "text/html": HtmlExtractor,
            "application/xhtml+xml": HtmlExtractor,
            # XML / JATS
            "application/xml": XmlExtractor,
            "text/xml": XmlExtractor,
            # LaTeX
            "text/x-tex": LatexExtractor,
            "application/x-tex": LatexExtractor,
        }
        self._instances: Dict[str, BaseExtractor] = {}

    def create(self, mime_type: str) -> BaseExtractor:
        """Return extractor for the MIME type, caching instances."""
        if mime_type not in self._creators:
            supported = ", ".join(sorted(self._creators))
            raise ValueError(
                f"Unsupported MIME type: {mime_type}. Supported: {supported}"
            )

        if mime_type not in self._instances:
            extractor_cls = self._creators[mime_type]
            self._instances[mime_type] = extractor_cls()

        return self._instances[mime_type]

    def supports(self, mime_type: str) -> bool:
        return mime_type in self._creators
