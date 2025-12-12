from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from ArticleCrawler.api.api_factory import create_api_provider
from ArticleCrawler.api.base_api import BaseAPIProvider

from app.core.exceptions import InvalidInputException
from app.schemas.seed_session import SeedSession
from app.schemas.seeds import MatchedSeed, SeedMatchResult, UnmatchedSeed


@dataclass
class SeedAdditionResult:
    added_count: int
    duplicate_count: int
    total_seeds: int


class SeedSessionManager:
    """Encapsulate mutation logic for seed sessions."""

    def add_seeds(self, session: SeedSession, seeds: Sequence[MatchedSeed]) -> SeedAdditionResult:
        existing_ids = {seed.paper_id for seed in session.seeds}
        added = 0
        duplicates = 0
        for seed in seeds:
            if seed.paper_id in existing_ids:
                duplicates += 1
                continue
            session.seeds.append(seed)
            existing_ids.add(seed.paper_id)
            added += 1
        session.updated_at = datetime.now(timezone.utc)
        return SeedAdditionResult(added_count=added, duplicate_count=duplicates, total_seeds=len(session.seeds))

    def replace_seeds(self, session: SeedSession, seeds: Sequence[MatchedSeed]) -> SeedAdditionResult:
        session.seeds = list(seeds)
        session.updated_at = datetime.now(timezone.utc)
        return SeedAdditionResult(added_count=len(session.seeds), duplicate_count=0, total_seeds=len(session.seeds))

    def remove_seed(self, session: SeedSession, paper_id: str) -> bool:
        before = len(session.seeds)
        session.seeds = [seed for seed in session.seeds if seed.paper_id != paper_id]
        if len(session.seeds) != before:
            session.updated_at = datetime.now(timezone.utc)
            return True
        return False


class SeedMatchClientFactory:
    """Cache API clients for seed matching."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._cache: Dict[str, BaseAPIProvider] = {}

    def get_client(self, provider: str) -> BaseAPIProvider:
        normalized = (provider or "openalex").lower()
        if normalized not in self._cache:
            self._logger.debug("Creating seed selection API client for %s", normalized)
            self._cache[normalized] = create_api_provider(normalized)
        return self._cache[normalized]


class PaperMetadataFetcher:
    """Fetch paper metadata from configured API providers."""

    def __init__(self, client_factory: SeedMatchClientFactory, logger: Optional[logging.Logger] = None):
        self._client_factory = client_factory
        self._logger = logger or logging.getLogger(__name__)

    def fetch(self, provider: str, paper_id: str) -> Optional[object]:
        api = self._client_factory.get_client(provider)
        try:
            if provider == "openalex" and hasattr(api, "get_paper_metadata_only"):
                return api.get_paper_metadata_only(paper_id)
            return api.get_paper(paper_id)
        except Exception as exc:
            self._logger.warning("Failed to fetch paper %s via %s: %s", paper_id, provider, exc)
            return None


class SeedMatchBuilder:
    """Convert provider responses into MatchedSeed objects."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        provider_builders: Optional[Dict[str, Callable[[Any, str], MatchedSeed]]] = None,
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._builders: Dict[str, Callable[[Any, str], MatchedSeed]] = {
            "openalex": self._from_openalex,
            "semantic_scholar": self._from_semantic_scholar,
        }
        for key, builder in (provider_builders or {}).items():
            self.register_builder(key, builder)

    def build(self, provider: str, paper_data, original_id: str) -> MatchedSeed:
        normalized = (provider or "").lower()
        handler = self._builders.get(normalized)
        if not handler:
            raise InvalidInputException(f"Unknown provider: {provider}")
        return handler(paper_data, original_id)

    def register_builder(self, provider: str, builder: Callable[[Any, str], MatchedSeed]) -> None:
        key = (provider or "").lower()
        if not key:
            raise InvalidInputException("Provider name cannot be empty")
        self._builders[key] = builder

    def _from_openalex(self, paper_data, original_id: str) -> MatchedSeed:
        if isinstance(paper_data, dict):
            return self._from_openalex_dict(paper_data, original_id)
        return self._from_openalex_object(paper_data, original_id)

    def _from_openalex_dict(self, paper_data: Dict, original_id: str) -> MatchedSeed:
        paper_id = paper_data.get("id", "") or ""
        if "/" in paper_id:
            paper_id = paper_id.split("/")[-1]
        title = paper_data.get("title")
        authors = self._author_summary(paper_data.get("authorships") or [])
        year = paper_data.get("publication_year")
        venue = self._extract_venue(paper_data.get("primary_location"))
        cited_by = paper_data.get("cited_by_count")
        references = paper_data.get("referenced_works")
        references_count = len(references) if isinstance(references, list) else None
        doi = paper_data.get("doi") or None
        landing_url = None
        primary_location = paper_data.get("primary_location") or {}
        if isinstance(primary_location, dict):
            landing_url = primary_location.get("landing_page_url") or None
        abstract = paper_data.get("abstract") or self._build_abstract_from_index(paper_data.get("abstract_inverted_index"))
        institutions = self._institutions_from_authorships(paper_data.get("authorships") or [])

        return MatchedSeed(
            paper_id=paper_id,
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            confidence=1.0,
            match_method="Direct ID" if original_id == paper_id else "API Lookup",
            cited_by_count=cited_by if isinstance(cited_by, int) else None,
            references_count=references_count,
            doi=doi,
            url=landing_url,
            abstract=abstract,
            institutions=institutions,
        )

    def _from_openalex_object(self, paper_data, original_id: str) -> MatchedSeed:
        paper_id = getattr(paper_data, "id", None)
        if isinstance(paper_id, str) and "/" in paper_id:
            paper_id = paper_id.split("/")[-1]
        title = getattr(paper_data, "title", None)
        authors = self._author_summary(getattr(paper_data, "authorships", None) or [])
        year = getattr(paper_data, "publication_year", None)
        venue = None
        primary_location = getattr(paper_data, "primary_location", None)
        if primary_location and getattr(primary_location, "source", None):
            venue = getattr(primary_location.source, "display_name", None)
        cited_by = getattr(paper_data, "cited_by_count", None)
        references = getattr(paper_data, "referenced_works", None)
        references_count = len(references) if isinstance(references, list) else None
        doi = getattr(paper_data, "doi", None)
        landing_url = getattr(primary_location, "landing_page_url", None) if primary_location else None
        abstract = getattr(paper_data, "abstract", None) or self._build_abstract_from_index(
            getattr(paper_data, "abstract_inverted_index", None)
        )
        institutions = self._institutions_from_authorships(getattr(paper_data, "authorships", None) or [])

        return MatchedSeed(
            paper_id=paper_id or original_id,
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            confidence=1.0,
            match_method="Direct ID" if original_id == paper_id else "API Lookup",
            cited_by_count=cited_by if isinstance(cited_by, int) else None,
            references_count=references_count,
            doi=doi,
            url=landing_url,
            abstract=abstract,
            institutions=institutions,
        )

    def _from_semantic_scholar(self, paper_data, original_id: str) -> MatchedSeed:
        if isinstance(paper_data, dict):
            paper_id = paper_data.get("paperId", "")
            title = paper_data.get("title")
            authors = self._author_summary(paper_data.get("authors") or [])
            year = paper_data.get("year")
            venue = paper_data.get("venue")
        else:
            paper_id = getattr(paper_data, "paperId", None) or str(paper_data)
            title = getattr(paper_data, "title", None)
            authors = self._author_summary(getattr(paper_data, "authors", None) or [])
            year = getattr(paper_data, "year", None)
            venue = getattr(paper_data, "venue", None)
        if "/" in str(paper_id):
            paper_id = str(paper_id).split("/")[-1]
        return MatchedSeed(
            paper_id=paper_id,
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            confidence=1.0,
            match_method="Direct ID" if original_id == paper_id else "API Lookup",
        )

    def _author_summary(self, authorships: Iterable) -> Optional[str]:
        names: List[str] = []
        for entry in list(authorships)[:3]:
            if isinstance(entry, dict):
                author = entry.get("author", {})
                name = author.get("display_name") or author.get("name") or ""
            else:
                name = getattr(getattr(entry, "author", entry), "display_name", None) or getattr(entry, "name", "")
            if name:
                names.append(name)
        if not names:
            return None
        summary = ", ".join(names)
        if len(list(authorships)) > 3:
            summary += " et al."
        return summary

    def _extract_venue(self, primary_location) -> Optional[str]:
        if isinstance(primary_location, dict):
            source = primary_location.get("source") or {}
            return source.get("display_name")
        if primary_location and getattr(primary_location, "source", None):
            return getattr(primary_location.source, "display_name", None)
        return None

    def _build_abstract_from_index(self, inverted_index) -> Optional[str]:
        if not isinstance(inverted_index, dict):
            return None
        try:
            max_pos = 0
            for word, positions in inverted_index.items():
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

    def _institutions_from_authorships(self, authorships: Iterable) -> Optional[List[str]]:
        names: List[str] = []
        for entry in authorships:
            institutions = None
            if isinstance(entry, dict):
                institutions = entry.get("institutions")
            elif hasattr(entry, "institutions"):
                institutions = entry.institutions
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


class SeedAggregationHelper:
    """Combine multiple match results into a unique seed list."""

    def aggregate(self, match_results: List[SeedMatchResult]) -> List[MatchedSeed]:
        seeds: List[MatchedSeed] = []
        seen: set[str] = set()
        for result in match_results:
            for seed in result.matched_seeds:
                if seed.paper_id not in seen:
                    seen.add(seed.paper_id)
                    seeds.append(seed)
        return seeds


class SeedResultBuilder:
    """Compose matched/unmatched lists when processing IDs."""

    def __init__(self, match_builder: SeedMatchBuilder, logger: Optional[logging.Logger] = None):
        self._match_builder = match_builder
        self._logger = logger or logging.getLogger(__name__)

    def process(
        self,
        provider: str,
        paper_id: str,
        metadata: Optional[object],
    ) -> Tuple[Optional[MatchedSeed], Optional[UnmatchedSeed]]:
        if metadata is None:
            return None, UnmatchedSeed(input_id=paper_id, error="Paper not found in API")
        try:
            matched = self._match_builder.build(provider, metadata, paper_id)
            return matched, None
        except Exception as exc:
            self._logger.error("Failed to build seed for %s: %s", paper_id, exc)
            return None, UnmatchedSeed(input_id=paper_id, error=str(exc))
