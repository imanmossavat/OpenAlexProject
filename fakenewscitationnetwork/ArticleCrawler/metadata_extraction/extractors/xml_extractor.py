import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

from .base import BaseExtractor
from ..models import PaperMetadata


class XmlExtractor(BaseExtractor):
    """Extract metadata from JATS/PMC style XML documents."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def extract(self, path: str) -> PaperMetadata:
        path_obj = Path(path)
        if not path_obj.exists():
            self._logger.error("XML file not found: %s", path)
            return PaperMetadata()

        try:
            tree = ET.parse(str(path_obj))
        except Exception as exc:
            self._logger.error("Failed to parse XML %s: %s", path, exc)
            return PaperMetadata()

        root = tree.getroot()

        title = self._text(root.find(".//{*}article-title"))
        authors = self._extract_authors(root)
        abstract = self._extract_abstract(root)
        year = self._text(root.find(".//{*}pub-date/{*}year"))
        if not year:
            year = self._text(root.find(".//{*}year"))
        doi = self._text(
            root.find(".//{*}article-id[@pub-id-type='doi']")
        ) or self._text(root.find(".//{*}id[@pub-id-type='doi']"))
        venue = self._text(root.find(".//{*}journal-title"))

        return PaperMetadata(
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            doi=doi,
            venue=venue,
        )

    def _text(self, element: Optional[ET.Element]) -> Optional[str]:
        if element is None:
            return None
        value = "".join(element.itertext()).strip()
        return value or None

    def _extract_authors(self, root: ET.Element) -> List[str]:
        authors = []
        contribs = root.findall(".//{*}contrib[@contrib-type='author']")
        if not contribs:
            contribs = root.findall(".//{*}author")

        for contrib in contribs:
            surname = self._text(contrib.find(".//{*}surname"))
            given = self._text(contrib.find(".//{*}given-names"))
            if given and surname:
                authors.append(f"{given} {surname}")
            elif surname:
                authors.append(surname)
            elif given:
                authors.append(given)
        return authors

    def _extract_abstract(self, root: ET.Element) -> Optional[str]:
        abstract_el = root.find(".//{*}abstract")
        if abstract_el is None:
            return None
        text = " ".join(t.strip() for t in abstract_el.itertext() if t.strip())
        return text or None
