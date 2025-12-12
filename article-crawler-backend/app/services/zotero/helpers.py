from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ArticleCrawler.api.zotero.client import ZoteroClient
from ArticleCrawler.api.zotero.metadata_extractor import ZoteroMetadataExtractor
from ArticleCrawler.api.zotero.matching.matcher import MatchResult, ZoteroMatcher

from app.schemas.zotero_seeds import (
    ZoteroCollection,
    ZoteroItemMetadata,
    ZoteroMatchCandidate,
    ZoteroMatchResult,
)
from app.schemas.seeds import MatchedSeed
from app.services.providers.article_crawler import ArticleCrawlerAPIProviderFactory


class ZoteroClientAdapter:
    """Adapter around the ArticleCrawler Zotero client."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    def get_client(self) -> ZoteroClient:
        return ZoteroClient(logger=self._logger)


class ZoteroMetadataExtractorAdapter:
    """Adapter that exposes the metadata extractor."""

    def __init__(self, extractor: Optional[ZoteroMetadataExtractor] = None):
        self._extractor = extractor or ZoteroMetadataExtractor()

    def extract(self, item) -> Dict:
        return self._extractor.extract(item)


class ZoteroMatcherAdapter:
    """Adapter around the ArticleCrawler matcher."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    def match_items(self, api_provider, items_metadata: Sequence[Dict]) -> List[MatchResult]:
        matcher = ZoteroMatcher(api_provider, logger=self._logger)
        return matcher.match_items(items_metadata)


@dataclass
class ZoteroSessionState:
    items: Dict[str, ZoteroItemMetadata] = field(default_factory=dict)
    match_results: List[ZoteroMatchResult] = field(default_factory=list)
    collections: Dict[str, str] = field(default_factory=dict)
    manual_selections: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class ZoteroSessionStore:
    """In-memory session storage for staged Zotero items and match results."""

    def __init__(self):
        self._sessions: Dict[str, ZoteroSessionState] = {}

    def get_or_create(self, session_id: str) -> ZoteroSessionState:
        return self._sessions.setdefault(session_id, ZoteroSessionState())

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


class ZoteroMatchResultBuilder:
    """Convert ArticleCrawler match outputs into API schema objects."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    def build_results(self, match_results: Iterable[MatchResult]) -> List[ZoteroMatchResult]:
        results: List[ZoteroMatchResult] = []
        for match_result in match_results:
            candidates = [
                ZoteroMatchCandidate(
                    paper_id=candidate.paper_id,
                    title=candidate.title,
                    similarity=candidate.similarity,
                    year=candidate.year,
                    venue=candidate.venue,
                    doi=candidate.doi,
                )
                for candidate in match_result.candidates
            ]
            results.append(
                ZoteroMatchResult(
                    zotero_key=match_result.zotero_key,
                    title=match_result.title,
                    matched=match_result.matched,
                    paper_id=match_result.paper_id,
                    confidence=match_result.confidence,
                    match_method=match_result.match_method,
                    error=match_result.error,
                    candidates=candidates,
                )
            )
        return results


class ZoteroSeedEnricher:
    """Fetch additional metadata for matched seeds."""

    def __init__(self, api_factory: ArticleCrawlerAPIProviderFactory, logger: Optional[logging.Logger] = None):
        self._api_factory = api_factory
        self._logger = logger or logging.getLogger(__name__)

    def fetch_details(self, provider: str, paper_id: str):
        try:
            api = self._api_factory.get_provider(provider)
        except Exception as exc:
            self._logger.warning("Unable to create API provider %s: %s", provider, exc)
            return None
        try:
            if hasattr(api, "get_paper_metadata_only"):
                return api.get_paper_metadata_only(paper_id)
            return api.get_paper(paper_id)
        except Exception as exc:
            self._logger.warning("Failed to fetch paper %s for enrichment: %s", paper_id, exc)
            return None

    def enrich_seed(self, provider: str, paper_id: str) -> Dict:
        paper = self.fetch_details(provider, paper_id)
        if not paper:
            return {}
        extras = {
            "doi": None,
            "url": None,
            "abstract": None,
            "cited_by_count": None,
            "references_count": None,
            "institutions": None,
            "authors": None,
        }
        try:
            if isinstance(paper, dict):
                extras["doi"] = paper.get("doi")
                primary_location = paper.get("primary_location") or {}
                if isinstance(primary_location, dict):
                    extras["url"] = primary_location.get("landing_page_url")
                extras["cited_by_count"] = paper.get("cited_by_count")
                references = paper.get("referenced_works")
                extras["references_count"] = len(references) if isinstance(references, list) else None
                extras["abstract"] = paper.get("abstract")
                if not extras["abstract"]:
                    extras["abstract"] = self._build_abstract_from_index(paper.get("abstract_inverted_index"))
                extras["institutions"] = self._extract_institutions(paper.get("authorships") or [])
                extras["authors"] = self._format_authors_from_paper(paper)
            else:
                extras["doi"] = getattr(paper, "doi", None)
                primary_location = getattr(paper, "primary_location", None)
                if primary_location and hasattr(primary_location, "landing_page_url"):
                    extras["url"] = primary_location.landing_page_url
                extras["cited_by_count"] = getattr(paper, "cited_by_count", None)
                references = getattr(paper, "referenced_works", None)
                extras["references_count"] = len(references) if isinstance(references, list) else None
                extras["abstract"] = getattr(paper, "abstract", None) or self._build_abstract_from_index(
                    getattr(paper, "abstract_inverted_index", None)
                )
                extras["institutions"] = self._extract_institutions(getattr(paper, "authorships", None) or [])
                extras["authors"] = self._format_authors_from_paper(paper)
        except Exception:
            return extras
        return extras

    def _build_abstract_from_index(self, inverted_index) -> Optional[str]:
        if not isinstance(inverted_index, dict):
            return None
        try:
            max_pos = 0
            for positions in inverted_index.values():
                if positions:
                    max_pos = max(max_pos, max(positions))
            tokens = [""] * (max_pos + 1)
            for word, positions in inverted_index.items():
                for pos in positions:
                    tokens[pos] = word
            abstract = " ".join(filter(None, tokens))
            return abstract or None
        except Exception:
            return None

    def _extract_institutions(self, authorships: Iterable) -> Optional[List[str]]:
        names: List[str] = []
        for auth in authorships:
            institutions = None
            if isinstance(auth, dict):
                institutions = auth.get("institutions")
            elif hasattr(auth, "institutions"):
                institutions = auth.institutions
            for inst in institutions or []:
                if isinstance(inst, dict):
                    name = inst.get("display_name") or inst.get("name")
                else:
                    name = getattr(inst, "display_name", None) or getattr(inst, "name", None)
                if name:
                    names.append(name)
        if not names:
            return None
        dedup = []
        seen = set()
        for name in names:
            if name not in seen:
                seen.add(name)
                dedup.append(name)
        return dedup

    def _format_authors_from_paper(self, paper) -> Optional[str]:
        authors: List[str] = []
        try:
            authorships = None
            if isinstance(paper, dict):
                authorships = paper.get("authorships") or []
                for auth in authorships[:3]:
                    author = auth.get("author") if isinstance(auth, dict) else None
                    name = author.get("display_name") if isinstance(author, dict) else None
                    if name:
                        authors.append(name)
            else:
                authorships = getattr(paper, "authorships", None) or []
                for auth in authorships[:3]:
                    author = getattr(auth, "author", None)
                    name = getattr(author, "display_name", None) if author else None
                    if name:
                        authors.append(name)
            if not authors:
                return None
            author_str = ", ".join(authors)
            if authorships and len(authorships) > 3:
                author_str += " et al."
            return author_str
        except Exception:
            return None
