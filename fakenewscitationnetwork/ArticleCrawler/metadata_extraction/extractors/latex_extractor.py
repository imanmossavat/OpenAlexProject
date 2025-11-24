import logging
import re
from pathlib import Path
from typing import List, Optional

from pylatexenc.latex2text import LatexNodes2Text

from .base import BaseExtractor
from ..models import PaperMetadata
from ..utils import parse_author_list, find_doi


class LatexExtractor(BaseExtractor):
    """Extract metadata from LaTeX source files."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        converter: Optional[LatexNodes2Text] = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._converter = converter or LatexNodes2Text()

    def extract(self, path: str) -> PaperMetadata:
        path_obj = Path(path)
        if not path_obj.exists():
            self._logger.error("LaTeX file not found: %s", path)
            return PaperMetadata()

        try:
            text = path_obj.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            self._logger.error("Failed to read LaTeX %s: %s", path, exc)
            return PaperMetadata()

        title = self._find_and_clean(r"\\title\{(.+?)\}", text)
        authors_raw = self._find_and_clean(r"\\author\{(.+?)\}", text)
        authors = parse_author_list(authors_raw) if authors_raw else []
        abstract = self._find_and_clean(
            r"\\begin\{abstract\}(.+?)\\end\{abstract\}", text
        )
        year = self._find_year(text)
        doi = find_doi(text)

        return PaperMetadata(
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            doi=doi,
            venue=None,
        )

    def _find_and_clean(self, pattern: str, text: str) -> Optional[str]:
        match = re.search(pattern, text, flags=re.S)
        if not match:
            return None
        cleaned = self._converter.latex_to_text(match.group(1)).strip()
        return cleaned or None

    def _find_year(self, text: str) -> Optional[str]:
        match = re.search(r"\\date\{(\d{4})\}", text)
        if match:
            return match.group(1)
        return None
