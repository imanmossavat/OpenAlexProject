from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.core.exceptions import InvalidInputException
from app.schemas.seeds import MatchedSeed
from app.schemas.zotero_seeds import (
    ZoteroCollection,
    ZoteroItemMetadata,
    ZoteroMatchResult,
)
from app.services.providers.article_crawler import ArticleCrawlerAPIProviderFactory
from app.services.zotero.helpers import (
    ZoteroClientAdapter,
    ZoteroMatchResultBuilder,
    ZoteroMetadataExtractorAdapter,
    ZoteroMatcherAdapter,
    ZoteroSeedEnricher,
    ZoteroSessionStore,
)


class ZoteroSeedService:
    """Coordinate Zotero collection discovery, staging, and matching."""

    def __init__(
        self,
        logger: logging.Logger,
        client_adapter: Optional[ZoteroClientAdapter] = None,
        metadata_extractor: Optional[ZoteroMetadataExtractorAdapter] = None,
        matcher_adapter: Optional[ZoteroMatcherAdapter] = None,
        session_store: Optional[ZoteroSessionStore] = None,
        match_result_builder: Optional[ZoteroMatchResultBuilder] = None,
        seed_enricher: Optional[ZoteroSeedEnricher] = None,
        api_factory: Optional[ArticleCrawlerAPIProviderFactory] = None,
    ):
        self._logger = logger
        self._client_adapter = client_adapter or ZoteroClientAdapter(logger=logger)
        self._metadata_extractor = metadata_extractor or ZoteroMetadataExtractorAdapter()
        self._matcher_adapter = matcher_adapter or ZoteroMatcherAdapter(logger=logger)
        self._session_store = session_store or ZoteroSessionStore()
        self._match_result_builder = match_result_builder or ZoteroMatchResultBuilder(logger=logger)
        self._seed_enricher = seed_enricher or ZoteroSeedEnricher(
            api_factory=api_factory or ArticleCrawlerAPIProviderFactory(logger=logger),
            logger=logger,
        )
        self._api_factory = api_factory or ArticleCrawlerAPIProviderFactory(logger=logger)

    # ------------------------------------------------------------------ #
    # Availability & collection helpers
    # ------------------------------------------------------------------ #
    def check_zotero_availability(self) -> tuple[bool, Optional[str]]:
        try:
            self._client_adapter.get_client()
            return True, None
        except Exception as exc:
            self._logger.error("Zotero availability check failed: %s", exc)
            return False, str(exc)

    def get_collections(self, session_id: str) -> List[ZoteroCollection]:
        try:
            client = self._client_adapter.get_client()
            collections_raw = client.get_collections()
        except Exception as exc:
            self._logger.error("Unable to retrieve Zotero collections: %s", exc)
            raise InvalidInputException(f"Failed to retrieve Zotero collections: {exc}") from exc

        session = self._session_store.get_or_create(session_id)
        session.collections = {col["key"]: col["name"] for col in collections_raw}

        collections: List[ZoteroCollection] = []
        for col in collections_raw:
            parent = col["data"].get("parentCollection") or None
            if parent is False:
                parent = None
            collections.append(
                ZoteroCollection(
                    key=col["key"],
                    name=col["name"],
                    parent_collection=parent,
                )
            )
        self._logger.info("Fetched %s Zotero collections for session %s", len(collections), session_id)
        return collections

    def get_collection_items(self, session_id: str, collection_key: str) -> tuple[str, List[ZoteroItemMetadata]]:
        session = self._session_store.get_or_create(session_id)
        collection_name = session.collections.get(collection_key, "Unknown Collection")
        try:
            client = self._client_adapter.get_client()
            items = client.get_collection_items(collection_key)
        except Exception as exc:
            self._logger.error("Unable to retrieve Zotero items for %s: %s", collection_key, exc)
            raise InvalidInputException(f"Failed to retrieve Zotero collection items: {exc}") from exc

        items_metadata: List[ZoteroItemMetadata] = []
        for item in items:
            metadata_dict = self._metadata_extractor.extract(item)
            metadata_dict["collection_key"] = collection_key
            items_metadata.append(ZoteroItemMetadata(**metadata_dict))

        self._logger.info(
            "Retrieved %s Zotero items for collection %s (%s)",
            len(items_metadata),
            collection_key,
            collection_name,
        )
        return collection_name, items_metadata

    # ------------------------------------------------------------------ #
    # Staging operations
    # ------------------------------------------------------------------ #
    def stage_items(self, session_id: str, items: List[ZoteroItemMetadata]) -> int:
        session = self._session_store.get_or_create(session_id)
        staged = 0
        for item in items:
            if item.zotero_key not in session.items:
                session.items[item.zotero_key] = item
                staged += 1
        self._logger.info("Staged %s Zotero items for session %s", staged, session_id)
        return staged

    def get_staged_items(self, session_id: str) -> List[ZoteroItemMetadata]:
        session = self._session_store.get_or_create(session_id)
        return list(session.items.values())

    def remove_staged_item(self, session_id: str, zotero_key: str) -> None:
        session = self._session_store.get_or_create(session_id)
        if zotero_key not in session.items:
            raise InvalidInputException(f"Item {zotero_key} not found in staging area")
        session.items.pop(zotero_key, None)
        self._logger.info("Removed staged Zotero item %s for session %s", zotero_key, session_id)

    # ------------------------------------------------------------------ #
    # Matching workflow
    # ------------------------------------------------------------------ #
    def match_staged_items(self, session_id: str, api_provider: str = "openalex") -> List[ZoteroMatchResult]:
        session = self._session_store.get_or_create(session_id)
        if not session.items:
            self._logger.warning("No staged Zotero items to match for session %s", session_id)
            return []
        try:
            api = self._api_factory.get_provider(api_provider)
        except Exception as exc:
            self._logger.error("Unable to initialize API provider %s: %s", api_provider, exc)
            raise InvalidInputException(f"Unable to initialize API provider: {exc}") from exc

        metadata_payloads = [item.model_dump() for item in session.items.values()]
        match_results_raw = self._matcher_adapter.match_items(api, metadata_payloads)
        session.match_results = self._match_result_builder.build_results(match_results_raw)

        matched_count = sum(1 for result in session.match_results if result.matched)
        self._logger.info(
            "Matched %s/%s Zotero items for session %s",
            matched_count,
            len(session.match_results),
            session_id,
        )
        return session.match_results

    def get_match_results(self, session_id: str) -> List[ZoteroMatchResult]:
        return list(self._session_store.get_or_create(session_id).match_results)

    # ------------------------------------------------------------------ #
    # Manual selection helpers
    # ------------------------------------------------------------------ #
    def store_manual_selections(self, session_id: str, selections: List[Dict]) -> None:
        session = self._session_store.get_or_create(session_id)
        session.manual_selections = [self._normalize_selection(sel) for sel in selections]
        self._logger.info(
            "Stored %s manual selections for session %s",
            len(session.manual_selections),
            session_id,
        )

    def get_manual_selections(self, session_id: str) -> List[Dict]:
        session = self._session_store.get_or_create(session_id)
        return list(session.manual_selections)

    def clear_manual_selections(self, session_id: str) -> None:
        session = self._session_store.get_or_create(session_id)
        session.manual_selections.clear()

    # ------------------------------------------------------------------ #
    # Confirmation / seed building
    # ------------------------------------------------------------------ #
    def get_confirmed_seeds(
        self,
        session_id: str,
        action: str,
        manual_selections: Optional[List[Dict]] = None,
    ) -> List[MatchedSeed]:
        if action == "skip_all":
            self._logger.info("User skipped all Zotero matches for session %s", session_id)
            return []

        session = self._session_store.get_or_create(session_id)
        match_results = session.match_results or []
        if not match_results:
            raise InvalidInputException("No match results found. Please run match first.")

        normalized_manual = [self._normalize_selection(sel) for sel in (manual_selections or [])]
        if normalized_manual:
            session.manual_selections = normalized_manual
        else:
            normalized_manual = list(session.manual_selections)

        matched_lookup = {result.zotero_key: result for result in match_results}
        auto_seeds = self._build_auto_seeds(session, match_results)
        manual_seeds = self._build_manual_seeds(session, normalized_manual, matched_lookup)

        total_auto = len(auto_seeds)
        total_manual = len(manual_seeds)
        self._logger.info(
            "Prepared %s auto-matched seeds and %s manual seeds for session %s",
            total_auto,
            total_manual,
            session_id,
        )
        return auto_seeds + manual_seeds

    def _build_auto_seeds(self, session, match_results: List[ZoteroMatchResult]) -> List[MatchedSeed]:
        seeds: List[MatchedSeed] = []
        for result in match_results:
            if not result.matched or not result.paper_id:
                continue
            item = session.items.get(result.zotero_key)
            if not item:
                continue
            extras = self._seed_enricher.enrich_seed("openalex", result.paper_id) if result.paper_id else {}
            authors = self._format_authors(item.authors) or extras.get("authors")
            source_label = self._build_source_label(session.collections, getattr(item, "collection_key", None))
            seeds.append(
                MatchedSeed(
                    paper_id=result.paper_id,
                    title=item.title,
                    authors=authors,
                    year=item.year,
                    venue=item.publication or None,
                    confidence=result.confidence,
                    match_method=result.match_method or "auto",
                    doi=extras.get("doi"),
                    url=extras.get("url"),
                    abstract=extras.get("abstract"),
                    cited_by_count=extras.get("cited_by_count"),
                    references_count=extras.get("references_count"),
                    institutions=extras.get("institutions"),
                    source=source_label,
                    source_type="zotero",
                    source_id=item.zotero_key,
                )
            )
        return seeds

    def _build_manual_seeds(
        self,
        session,
        manual_selections: List[Dict],
        matched_lookup: Dict[str, ZoteroMatchResult],
    ) -> List[MatchedSeed]:
        seeds: List[MatchedSeed] = []
        for selection in manual_selections:
            if selection.get("action") != "select":
                continue
            zotero_key = selection.get("zotero_key")
            selected_paper_id = selection.get("selected_paper_id")
            if not zotero_key or not selected_paper_id:
                continue
            match_result = matched_lookup.get(zotero_key)
            if not match_result:
                self._logger.warning("Manual selection for %s has no match result", zotero_key)
                continue
            candidate = next(
                (cand for cand in match_result.candidates or [] if cand.paper_id == selected_paper_id),
                None,
            )
            if not candidate:
                self._logger.warning("Manual selection %s does not match any candidate", selected_paper_id)
                continue
            extras = self._seed_enricher.enrich_seed("openalex", selected_paper_id)
            authors = extras.get("authors")
            item = session.items.get(zotero_key)
            if not authors:
                authors = self._format_authors(item.authors if item else None)
            source_label = self._build_source_label(
                session.collections,
                getattr(item, "collection_key", None) if item else None,
            )
            seeds.append(
                MatchedSeed(
                    paper_id=candidate.paper_id,
                    title=candidate.title,
                    authors=authors,
                    year=candidate.year,
                    venue=candidate.venue,
                    confidence=candidate.similarity,
                    match_method="manual_selection",
                    doi=extras.get("doi"),
                    url=extras.get("url"),
                    abstract=extras.get("abstract"),
                    cited_by_count=extras.get("cited_by_count"),
                    references_count=extras.get("references_count"),
                    institutions=extras.get("institutions"),
                    source=source_label,
                    source_type="zotero",
                    source_id=zotero_key,
                )
            )
        return seeds

    # ------------------------------------------------------------------ #
    # Cleanup helpers
    # ------------------------------------------------------------------ #
    def clear_staging(self, session_id: str) -> None:
        session = self._session_store.get_or_create(session_id)
        session.items.clear()
        session.match_results.clear()
        session.manual_selections.clear()
        self._logger.info("Cleared staged Zotero items for session %s", session_id)

    def cleanup_session(self, session_id: str) -> None:
        self._session_store.clear(session_id)
        self._logger.info("Cleaned up Zotero session %s", session_id)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _format_authors(self, authors: Optional[List[str]]) -> Optional[str]:
        if not authors:
            return None
        summary = ", ".join(authors[:3])
        if len(authors) > 3:
            summary += " et al."
        return summary

    def _build_source_label(self, collections: Dict[str, str], collection_key: Optional[str]) -> str:
        if collection_key and collection_key in collections:
            return f"Zotero - {collections[collection_key]}"
        return "Zotero"

    def _normalize_selection(self, selection: Dict) -> Dict:
        if hasattr(selection, "model_dump"):
            selection = selection.model_dump()
        return {
            "zotero_key": selection.get("zotero_key"),
            "action": selection.get("action"),
            "selected_paper_id": selection.get("selected_paper_id"),
        }
