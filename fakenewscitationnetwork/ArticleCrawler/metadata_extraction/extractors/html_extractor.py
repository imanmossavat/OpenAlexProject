import logging
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup

from .base import BaseExtractor
from ..models import PaperMetadata


class HtmlExtractor(BaseExtractor):
    """Extract metadata from HTML files using citation meta tags."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def extract(self, path: str) -> PaperMetadata:
        path_obj = Path(path)
        if not path_obj.exists():
            self._logger.error("HTML file not found: %s", path)
            return PaperMetadata()

        try:
            html = path_obj.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            self._logger.error("Unable to read HTML %s: %s", path, exc)
            return PaperMetadata()

        soup = BeautifulSoup(html, "html.parser")

        title = self._get_meta(soup, "citation_title") or self._fallback_title(soup)
        authors = self._extract_authors(soup)
        abstract = self._get_meta(soup, "citation_abstract") or self._abstract_from_dom(
            soup
        )
        year = self._get_meta(soup, "citation_publication_date")
        doi = self._get_meta(soup, "citation_doi")
        venue = self._get_meta(soup, "citation_journal_title")

        return PaperMetadata(
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            doi=doi,
            venue=venue,
        )

    def _get_meta(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        author_tags = soup.find_all("meta", attrs={"name": "citation_author"})
        authors = []
        for tag in author_tags:
            content = tag.get("content")
            if content:
                authors.append(content.strip())
        return authors

    def _abstract_from_dom(self, soup: BeautifulSoup) -> Optional[str]:
        abstract_section = soup.find(id="abstract") or soup.find(class_="abstract")
        if abstract_section:
            text = abstract_section.get_text(separator=" ", strip=True)
            return text or None
        return None

    def _fallback_title(self, soup: BeautifulSoup) -> Optional[str]:
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return None
