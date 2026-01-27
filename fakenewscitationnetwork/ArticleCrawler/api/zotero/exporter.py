from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Dict, List, Optional, Sequence, Tuple

from ArticleCrawler.api.api_factory import create_api_provider
from ArticleCrawler.api.base_api import BaseAPIProvider
from ArticleCrawler.library.models import PaperData

from .client import ZoteroClient


@dataclass
class PaperExportPayload:
    """Metadata describing a paper that should be exported to Zotero."""

    paper_id: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ZoteroExportOptions:
    """Options governing a Zotero export transaction."""

    collection_key: Optional[str] = None
    collection_name: Optional[str] = None
    create_collection: bool = False
    dedupe: bool = True
    extra_tags: List[str] = field(default_factory=list)


@dataclass
class ZoteroExportResult:
    """Result counters for an export run."""

    created: List[str] = field(default_factory=list)
    skipped: Dict[str, str] = field(default_factory=dict)
    failed: Dict[str, str] = field(default_factory=dict)


class ZoteroExportService:
    """Encapsulates the workflow for exporting crawler papers into Zotero."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        client: Optional[ZoteroClient] = None,
        api_provider: Optional[BaseAPIProvider] = None,
        provider_name: str = "openalex",
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._client = client or ZoteroClient(logger=self._logger)
        self._api_provider = api_provider or create_api_provider(provider_name, logger=self._logger)

    def export_papers(
        self,
        papers: Sequence[PaperExportPayload],
        options: ZoteroExportOptions,
    ) -> ZoteroExportResult:
        """Export the provided papers to Zotero using the requested collection."""
        result = ZoteroExportResult()
        if not papers:
            return result

        collection_key = self._resolve_collection(options)
        if not collection_key:
            raise ValueError("A valid Zotero collection is required before exporting.")

        existing_identifiers: Dict[str, str] = {}
        if options.dedupe:
            existing_identifiers = self._build_identifier_lookup(collection_key)

        queued: List[Tuple[str, Dict]] = []
        for payload in papers:
            try:
                enriched = self._hydrate_payload(payload)
            except Exception as exc:
                self._logger.error("Unable to hydrate metadata for %s: %s", payload.paper_id, exc)
                result.failed[payload.paper_id] = str(exc)
                continue

            identifier = self._resolve_identifier(enriched)
            if options.dedupe and identifier and identifier in existing_identifiers:
                result.skipped[payload.paper_id] = "Duplicate DOI/URL already present in collection."
                continue

            item_payload = self._build_item_payload(enriched, collection_key, options.extra_tags)
            queued.append((payload.paper_id, item_payload))
            if identifier:
                existing_identifiers[identifier] = payload.paper_id

        if not queued:
            return result

        try:
            response = self._client.create_items([entry[1] for entry in queued])
        except Exception as exc:
            self._logger.error("Failed to create Zotero items: %s", exc)
            for paper_id, _ in queued:
                result.failed[paper_id] = str(exc)
            return result

        success_map = response.get("success") or response.get("successful") or {}
        failed_map = response.get("failed") or response.get("unprocessable") or {}

        processed = set()
        for idx_str, _ in success_map.items():
            try:
                idx = int(idx_str)
            except (ValueError, TypeError):
                continue
            if 0 <= idx < len(queued):
                paper_id = queued[idx][0]
                result.created.append(paper_id)
                processed.add(idx)

        failure_reason = failed_map or response.get("errors") or {}
        if isinstance(failure_reason, dict):
            for idx_str, details in failure_reason.items():
                try:
                    idx = int(idx_str)
                except (ValueError, TypeError):
                    continue
                if 0 <= idx < len(queued):
                    paper_id = queued[idx][0]
                    message = str(details)
                    result.failed[paper_id] = message
                    processed.add(idx)

        for idx, (paper_id, _) in enumerate(queued):
            if idx in processed:
                continue
            if paper_id not in result.failed:
                result.created.append(paper_id)

        return result

    def _resolve_collection(self, options: ZoteroExportOptions) -> Optional[str]:
        if options.collection_key:
            return options.collection_key
        if not options.collection_name:
            return None
        existing = self._client.get_collection_by_name(options.collection_name)
        if existing:
            return existing["key"]
        if options.create_collection:
            created = self._client.create_collection(options.collection_name)
            return created.get("key")
        return None

    def _build_identifier_lookup(self, collection_key: str) -> Dict[str, str]:
        identifiers: Dict[str, str] = {}
        try:
            items = self._client.list_all_collection_items(collection_key, batch_size=100)
        except Exception as exc:
            self._logger.warning("Unable to load existing Zotero items for deduplication: %s", exc)
            return identifiers

        for item in items:
            data = item.get("data") or {}
            doi = (data.get("DOI") or "").strip().lower()
            url = (data.get("url") or "").strip().lower()
            if doi:
                identifiers[f"doi:{doi}"] = data.get("title") or ""
            if url:
                identifiers[f"url:{url}"] = data.get("title") or ""
        return identifiers

    def _hydrate_payload(self, payload: PaperExportPayload) -> PaperExportPayload:
        needs_metadata = not payload.title or not payload.abstract or not payload.authors
        if not needs_metadata:
            return payload
        paper_data = self._fetch_metadata(payload.paper_id)
        if not paper_data:
            raise ValueError(f"Unable to fetch metadata for paper {payload.paper_id}")
        payload.title = payload.title or paper_data.title
        payload.abstract = payload.abstract or paper_data.abstract
        payload.authors = payload.authors or [auth.get("name") for auth in paper_data.authors if auth.get("name")]
        payload.year = payload.year or paper_data.year
        payload.venue = payload.venue or paper_data.venue
        payload.doi = payload.doi or paper_data.doi
        payload.url = payload.url or paper_data.url
        return payload

    def _fetch_metadata(self, paper_id: str) -> Optional[PaperData]:
        if not self._api_provider:
            return None
        if hasattr(self._api_provider, "get_paper_as_paper_data"):
            return self._api_provider.get_paper_as_paper_data(paper_id)
        paper = self._api_provider.get_paper(paper_id)
        if isinstance(paper, PaperData):
            return paper
        if isinstance(paper, dict):
            converter = getattr(self._api_provider, "_convert_work_to_paper_data", None)
            if converter:
                try:
                    return converter(paper)  # type: ignore[misc]
                except Exception:
                    return None
        return None

    def _build_item_payload(
        self,
        payload: PaperExportPayload,
        collection_key: str,
        extra_tags: Optional[List[str]] = None,
    ) -> Dict:
        creators = [self._creator_from_name(name) for name in payload.authors or []]
        tags = list(dict.fromkeys((payload.tags or []) + (extra_tags or [])))

        data = {
            "itemType": "journalArticle",
            "title": payload.title or payload.paper_id,
            "abstractNote": payload.abstract or "",
            "publicationTitle": payload.venue or "",
            "date": str(payload.year) if payload.year else "",
            "url": payload.url or "",
            "DOI": payload.doi or "",
            "creators": creators,
            "tags": [{"tag": tag} for tag in tags if tag],
            "collections": [collection_key],
            "extra": f"Paper ID: {payload.paper_id}",
        }
        return data

    def _creator_from_name(self, name: str) -> Dict[str, str]:
        stripped = (name or "").strip()
        if not stripped:
            return {"creatorType": "author", "name": ""}
        parts = stripped.split()
        if len(parts) == 1:
            return {"creatorType": "author", "name": stripped, "fieldMode": 1}
        first = " ".join(parts[:-1])
        last = parts[-1]
        return {
            "creatorType": "author",
            "firstName": first,
            "lastName": last,
        }

    def _resolve_identifier(self, payload: PaperExportPayload) -> Optional[str]:
        if payload.doi:
            return f"doi:{payload.doi.strip().lower()}"
        if payload.url:
            return f"url:{payload.url.strip().lower()}"
        return None
