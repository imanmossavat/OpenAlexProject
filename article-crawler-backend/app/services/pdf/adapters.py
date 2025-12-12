from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from ArticleCrawler.pdf_processing.docker_manager import DockerManager
from ArticleCrawler.pdf_processing.api_matcher import APIMetadataMatcher
from ArticleCrawler.metadata_extraction import MetadataDispatcher

from app.schemas.pdf_seeds import PDFMetadata, PDFMatchResult


class GrobidManagerAdapter:
    """Adapter around the Docker manager used to check GROBID availability."""

    def __init__(self, logger: Optional[logging.Logger] = None, manager: Optional[DockerManager] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._manager = manager or DockerManager(logger=self._logger)

    def is_running(self) -> bool:
        return self._manager.is_grobid_running()


class MetadataExtractionAdapter:
    """Adapter around MetadataDispatcher."""

    def __init__(self, logger: Optional[logging.Logger] = None, dispatcher: Optional[MetadataDispatcher] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._dispatcher = dispatcher or MetadataDispatcher(logger=self._logger)

    def extract(self, file_path: str):
        return self._dispatcher.extract(file_path)


@dataclass
class _FallbackMatchResult:
    metadata: Any
    matched: bool = False
    paper_id: Optional[str] = None
    confidence: float = 0.0
    match_method: Optional[str] = None


class PDFMetadataMatcherAdapter:
    """Wrapper that performs metadata matching and handles bulk fallback."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    def match(self, api_provider, metadata_list: Sequence[Any]) -> List[Any]:
        matcher = APIMetadataMatcher(api_provider, logger=self._logger)
        try:
            return matcher.match_metadata(metadata_list)
        except Exception as exc:
            self._logger.warning("Bulk PDF metadata match failed, falling back to per-file matching: %s", exc)
            results: List[Any] = []
            for item in metadata_list:
                try:
                    results.append(matcher._match_single(item))  # noqa: SLF001
                except Exception as inner_exc:
                    self._logger.warning("Match failed for %s: %s", getattr(item, "filename", "unknown"), inner_exc)
                    results.append(_FallbackMatchResult(metadata=item))
            return results


class PDFMatchResultBuilder:
    """Transform ArticleCrawler match outputs into API schema objects."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    def build_results(self, api_provider, api_match_results: Iterable[Any]) -> Tuple[List[PDFMatchResult], int]:
        match_results: List[PDFMatchResult] = []
        matched_count = 0

        def _get(obj, name):
            if obj is None:
                return None
            if isinstance(obj, dict):
                return obj.get(name)
            return getattr(obj, name, None)

        for result in api_match_results:
            meta = getattr(result, "metadata", None)
            filename = _get(meta, "filename") or "unknown"
            title_orig = _get(meta, "title")
            authors_orig = _get(meta, "authors")
            year_orig = _get(meta, "year")
            doi_orig = _get(meta, "doi")
            venue_orig = _get(meta, "venue")

            metadata_payload = PDFMetadata(
                filename=filename,
                title=title_orig,
                authors=authors_orig,
                year=year_orig,
                doi=doi_orig,
                venue=venue_orig,
            )

            if getattr(result, "matched", False):
                paper_result = self._fetch_paper(api_provider, getattr(result, "paper_id", None))
                if paper_result is None:
                    match_results.append(
                        PDFMatchResult(
                            filename=filename,
                            metadata=metadata_payload,
                            matched=False,
                        )
                    )
                    continue

                title = self._extract_title(paper_result)
                authors = self._extract_authors(paper_result)
                year = self._extract_year(paper_result)
                venue = self._extract_venue(paper_result)

                match_results.append(
                    PDFMatchResult(
                        filename=filename,
                        metadata=metadata_payload,
                        matched=True,
                        paper_id=getattr(result, "paper_id", None),
                        title=title,
                        authors=authors,
                        year=year,
                        venue=venue,
                        confidence=getattr(result, "confidence", None),
                        match_method=getattr(result, "match_method", None),
                    )
                )
                matched_count += 1
            else:
                match_results.append(PDFMatchResult(filename=filename, metadata=metadata_payload, matched=False))

        return match_results, matched_count

    def _fetch_paper(self, api_provider, paper_id: Optional[str]):
        if not paper_id or api_provider is None:
            return None
        try:
            if hasattr(api_provider, "get_paper_metadata_only"):
                return api_provider.get_paper_metadata_only(paper_id)
            return api_provider.get_paper(paper_id)
        except Exception as exc:
            self._logger.warning("Failed to fetch paper %s: %s", paper_id, exc)
            return None

    def _extract_title(self, paper) -> Optional[str]:
        if isinstance(paper, dict):
            return paper.get("title")
        return getattr(paper, "title", None)

    def _extract_authors(self, paper) -> Optional[str]:
        authors_list = None
        if isinstance(paper, dict):
            authors_list = paper.get("authorships", [])
            names = [a.get("author", {}).get("display_name", "") for a in authors_list[:3]]
        else:
            authors_list = getattr(paper, "authorships", [])
            names = []
            for auth in authors_list[:3]:
                author_obj = getattr(auth, "author", None)
                name = getattr(author_obj, "display_name", None) if author_obj else None
                if name:
                    names.append(name)
        names = [name for name in names if name]
        if not names:
            return None
        author_summary = ", ".join(names)
        if len(authors_list) > 3:
            author_summary += " et al."
        return author_summary

    def _extract_year(self, paper) -> Optional[int]:
        if isinstance(paper, dict):
            return paper.get("publication_year")
        return getattr(paper, "publication_year", None)

    def _extract_venue(self, paper) -> Optional[str]:
        if isinstance(paper, dict):
            primary_location = paper.get("primary_location") or {}
            source = primary_location.get("source") or {}
            return source.get("display_name")
        primary_location = getattr(paper, "primary_location", None)
        if primary_location and getattr(primary_location, "source", None):
            return getattr(primary_location.source, "display_name", None)
        return None
