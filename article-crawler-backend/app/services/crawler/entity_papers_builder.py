from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from ArticleCrawler.api.base_api import BaseAPIProvider
from ArticleCrawler.crawler import Crawler
from ArticleCrawler.utils.url_builder import PaperURLBuilder


RemotePaperEntryBuilder = Callable[
    [str, Dict, str, PaperURLBuilder],
    Dict,
]


class RemoteEntityPapersBuilder:
    """Build paginated author/venue paper payloads using the configured API provider."""

    def __init__(
        self,
        logger,
        api_client_factory: Callable[[str], Optional[BaseAPIProvider]],
        *,
        max_page_size: int = 50,
    ) -> None:
        self.logger = logger
        self._api_client_factory = api_client_factory
        self._max_page_size = max_page_size
        self._url_builder = PaperURLBuilder()

    def build_author_papers(
        self,
        crawler: Crawler,
        author_id: str,
        *,
        page: int,
        page_size: int,
        entry_builder: RemotePaperEntryBuilder,
    ) -> Optional[Dict]:
        author_label = self._lookup_author_label(crawler, author_id)
        return self._build_remote_entity_papers(
            crawler,
            entity_type="author",
            entity_id=author_id,
            entity_label=author_label,
            fetcher=lambda api, p, size: api.get_author_papers(
                author_id, page=p, page_size=size
            ),
            page=page,
            page_size=page_size,
            entry_builder=entry_builder,
        )

    def build_venue_papers(
        self,
        crawler: Crawler,
        venue_id: str,
        *,
        page: int,
        page_size: int,
        entry_builder: RemotePaperEntryBuilder,
    ) -> Optional[Dict]:
        venue_label = self._lookup_venue_label(crawler, venue_id)
        return self._build_remote_entity_papers(
            crawler,
            entity_type="venue",
            entity_id=venue_id,
            entity_label=venue_label,
            fetcher=lambda api, p, size: api.get_venue_papers(
                venue_id, page=p, page_size=size
            ),
            page=page,
            page_size=page_size,
            entry_builder=entry_builder,
        )

    def _build_remote_entity_papers(
        self,
        crawler: Crawler,
        *,
        entity_type: str,
        entity_id: str,
        entity_label: Optional[str],
        fetcher: Callable[
            [BaseAPIProvider, int, int],
            Tuple[List, List[str], Optional[int]],
        ],
        page: int,
        page_size: int,
        entry_builder: RemotePaperEntryBuilder,
    ) -> Optional[Dict]:
        provider_type = getattr(
            getattr(crawler, "api_config", None),
            "provider_type",
            "openalex",
        )
        api_client = self._api_client_factory(provider_type)
        if not api_client:
            return None

        normalized_page_size = max(
            1,
            min(int(page_size or 1), self._max_page_size),
        )
        normalized_page = max(1, int(page or 1))

        try:
            papers, _, total_available = fetcher(
                api_client,
                normalized_page,
                normalized_page_size,
            )
        except NotImplementedError:
            self.logger.warning(
                "%s pagination not supported for provider %s",
                entity_type,
                provider_type,
            )
            return None
        except Exception as exc:
            self.logger.error(
                "Failed to retrieve %s papers for %s: %s",
                entity_type,
                entity_id,
                exc,
            )
            return None

        normalized_entries: List[Dict] = []
        for work in papers or []:
            normalized = self._normalize_provider_entry(
                work,
                provider_type,
            )
            if normalized:
                normalized_entries.append(normalized)

        entries = [
            entry_builder(
                entry["paper_id"],
                entry["fallback"],
                provider_type,
                self._url_builder,
            )
            for entry in normalized_entries
        ]

        total_count = self._resolve_total_count(
            total_available,
            normalized_page,
            normalized_page_size,
            len(entries),
        )

        label_value = entity_label or entity_id
        response = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_label": label_value,
            "page": normalized_page,
            "page_size": normalized_page_size,
            "total": total_count,
            "papers": entries,
        }
        response[f"{entity_type}_id"] = entity_id
        response[f"{entity_type}_label"] = label_value
        return response

    def _resolve_total_count(
        self,
        total_available: Optional[int],
        page: int,
        page_size: int,
        page_items: int,
    ) -> int:
        if total_available is None:
            return (page - 1) * page_size + page_items
        try:
            return int(total_available)
        except (TypeError, ValueError):
            return (page - 1) * page_size + page_items

    def _normalize_provider_entry(
        self,
        entry,
        provider_type: str,
    ) -> Optional[Dict]:
        paper_id = self._extract_identifier(entry)
        if not paper_id:
            return None

        title = self._extract_value(entry, "title", "display_name", "paperTitle")
        abstract = self._extract_value(entry, "abstract", "paperAbstract", "summary")
        year = self._extract_value(entry, "year", "publication_year", "publicationYear")
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None

        venue = self._extract_value(
            entry,
            "venue",
            "venue_display_name",
            "venueName",
        )
        if isinstance(venue, dict):
            venue = venue.get("display_name") or venue.get("name")

        doi = self._extract_value(entry, "doi")
        url = self._extract_value(entry, "url")
        if not url:
            url = self._url_builder.build_url(paper_id, provider_type)

        authors_list: List[str] = []
        authors_raw = self._extract_value(entry, "authors")
        if isinstance(authors_raw, list):
            for author_entry in authors_raw:
                if isinstance(author_entry, dict):
                    name = author_entry.get("name") or author_entry.get("display_name")
                else:
                    name = getattr(author_entry, "name", None) or getattr(
                        author_entry, "display_name", None
                    )
                if name:
                    authors_list.append(str(name))

        citation_count = self._extract_value(
            entry,
            "citation_count",
            "citationCount",
            "citedByCount",
            "cited_by_count",
            "numCitations",
        )

        fallback = {
            "paperId": paper_id,
            "title": title or paper_id,
            "abstract": abstract,
            "authors": authors_list,
            "year": year,
            "venue": venue,
            "doi": doi,
            "url": url,
        }
        if citation_count is not None:
            fallback["citation_count"] = citation_count

        return {
            "paper_id": paper_id,
            "fallback": fallback,
        }

    def _extract_identifier(self, entry) -> Optional[str]:
        value = self._extract_value(entry, "paper_id", "paperId", "id")
        if isinstance(value, str) and value.startswith("http"):
            value = value.split("/")[-1]
        return value

    def _extract_value(self, entry, *keys):
        for key in keys:
            if isinstance(entry, dict) and key in entry:
                return entry.get(key)
            if hasattr(entry, key):
                return getattr(entry, key)
        return None

    def _lookup_author_label(self, crawler: Crawler, author_id: str) -> str:
        df_author = getattr(crawler.data_coordinator.frames, "df_author", None)
        if df_author is not None and not df_author.empty:
            try:
                match = df_author[df_author["authorId"] == author_id]
                if not match.empty:
                    value = match.iloc[0].get("authorName")
                    if isinstance(value, str) and value.strip():
                        return value.strip()
            except Exception:
                pass
        return author_id

    def _lookup_venue_label(self, crawler: Crawler, venue_id: str) -> str:
        df_venues = getattr(crawler.data_coordinator.frames, "df_venue_features", None)
        if df_venues is not None and not df_venues.empty:
            try:
                if "venue_id" in df_venues.columns:
                    match = df_venues[df_venues["venue_id"] == venue_id]
                    if not match.empty:
                        value = match.iloc[0].get("venue")
                        if isinstance(value, str) and value.strip():
                            return value.strip()
                match = df_venues[df_venues["venue"] == venue_id]
                if not match.empty:
                    value = match.iloc[0].get("venue")
                    if isinstance(value, str) and value.strip():
                        return value.strip()
            except Exception:
                pass
        return venue_id
