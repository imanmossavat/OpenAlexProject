from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.schemas.seeds import MatchedSeed
from app.schemas.staging import StagingPaperCreate
from app.services.providers.article_crawler import ArticleCrawlerAPIProviderFactory


class _CallableAPIProviderFactory:
    """Adapter to allow passing a simple callable as the API factory."""

    def __init__(self, factory):
        self._factory = factory

    def get_provider(self, provider_name: str):
        return self._factory(provider_name)


class PDFStagingRowBuilder:
    """Transform reviewed PDF metadata into staging rows."""

    def build_from_reviewed(self, reviewed_metadata, stored_files: Dict[str, str]) -> List[StagingPaperCreate]:
        rows: List[StagingPaperCreate] = []
        for md in reviewed_metadata or []:
            file_id = stored_files.get(getattr(md, "filename", None))
            rows.append(
                StagingPaperCreate(
                    source="Uploaded Files",
                    source_type="pdf",
                    title=getattr(md, "title", None),
                    authors=getattr(md, "authors", None),
                    year=getattr(md, "year", None),
                    venue=getattr(md, "venue", None),
                    doi=getattr(md, "doi", None),
                    url=None,
                    abstract=getattr(md, "abstract", None),
                    source_id=getattr(md, "doi", None) or getattr(md, "filename", None),
                    source_file_id=file_id,
                    source_file_name=getattr(md, "filename", None) if file_id else None,
                    is_selected=False,
                )
            )
        return rows


class PDFMatchedSeedBuilder:
    """Build MatchedSeed objects from raw matching results."""

    def build(self, seeds_data: List[Dict]) -> List[MatchedSeed]:
        matched_seeds: List[MatchedSeed] = []
        for seed in seeds_data or []:
            matched_seeds.append(
                MatchedSeed(
                    paper_id=seed.get("paper_id"),
                    title=seed.get("title"),
                    authors=seed.get("authors"),
                    year=seed.get("year"),
                    venue=seed.get("venue"),
                    confidence=seed.get("confidence"),
                    match_method=seed.get("match_method"),
                    source="Uploaded Files",
                    source_type="pdf",
                    source_id=seed.get("source_id") or seed.get("paper_id"),
                )
            )
        return matched_seeds


class PDFSeedEnricher:
    """Enrich matched seeds with metadata from API providers."""

    def __init__(
        self,
        logger: logging.Logger,
        api_factory: Optional[ArticleCrawlerAPIProviderFactory] = None,
    ):
        self._logger = logger
        if api_factory is None:
            self._api_factory = ArticleCrawlerAPIProviderFactory(logger=logger)
        elif callable(api_factory) and not hasattr(api_factory, "get_provider"):
            self._api_factory = _CallableAPIProviderFactory(api_factory)
        else:
            self._api_factory = api_factory

    def enrich(self, seeds: List[MatchedSeed]) -> List[MatchedSeed]:
        if not seeds:
            return seeds

        try:
            api = self._api_factory.get_provider("openalex")
        except Exception:
            self._logger.exception("Unable to initialize OpenAlex provider for PDF enrichment")
            return seeds

        enriched: List[MatchedSeed] = []
        for seed in seeds:
            try:
                paper = (
                    api.get_paper_metadata_only(seed.paper_id)
                    if hasattr(api, "get_paper_metadata_only")
                    else api.get_paper(seed.paper_id)
                )
                extras = self._extract_enrichments(paper)
                enriched.append(
                    MatchedSeed(
                        paper_id=seed.paper_id,
                        title=seed.title,
                        authors=seed.authors,
                        year=seed.year,
                        venue=seed.venue,
                        confidence=seed.confidence,
                        match_method=seed.match_method,
                        doi=extras.get("doi"),
                        url=extras.get("url"),
                        abstract=extras.get("abstract"),
                        cited_by_count=extras.get("cited_by_count"),
                        references_count=extras.get("references_count"),
                        institutions=extras.get("institutions"),
                        source=seed.source,
                        source_type=seed.source_type,
                        source_id=seed.source_id,
                    )
                )
            except Exception:
                self._logger.warning("Unable to enrich paper %s", seed.paper_id, exc_info=True)
                enriched.append(seed)
        return enriched

    def _extract_enrichments(self, paper) -> Dict[str, Optional[object]]:
        extras: Dict[str, Optional[object]] = {
            "doi": None,
            "url": None,
            "abstract": None,
            "cited_by_count": None,
            "references_count": None,
            "institutions": None,
        }
        if not paper:
            return extras

        try:
            if isinstance(paper, dict):
                extras["cited_by_count"] = paper.get("cited_by_count") if isinstance(paper.get("cited_by_count"), int) else None
                refs = paper.get("referenced_works")
                extras["references_count"] = len(refs) if isinstance(refs, list) else None
                extras["doi"] = paper.get("doi") or None
                extras["url"] = self._extract_url_from_primary_location(paper.get("primary_location"))
                extras["abstract"] = self._resolve_abstract(paper.get("abstract"), paper.get("abstract_inverted_index"))
                extras["institutions"] = self._collect_institutions(paper.get("authorships"))
            else:
                cited = getattr(paper, "cited_by_count", None)
                extras["cited_by_count"] = cited if isinstance(cited, int) else None
                refs = getattr(paper, "referenced_works", None)
                extras["references_count"] = len(refs) if isinstance(refs, list) else None
                extras["doi"] = getattr(paper, "doi", None) if hasattr(paper, "doi") else None
                extras["url"] = self._extract_url_from_primary_location(getattr(paper, "primary_location", None))
                abstract = getattr(paper, "abstract", None)
                abstract_index = getattr(paper, "abstract_inverted_index", None)
                extras["abstract"] = self._resolve_abstract(abstract, abstract_index)
                extras["institutions"] = self._collect_institutions(getattr(paper, "authorships", None))
        except Exception:
            self._logger.exception("Failed to extract enrichment metadata")
        return extras

    def _resolve_abstract(self, abstract: Optional[str], inverted_index) -> Optional[str]:
        if abstract:
            return abstract
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
            return " ".join(token for token in tokens if token) or None
        except Exception:
            return None

    def _collect_institutions(self, authorships) -> Optional[List[str]]:
        if not authorships:
            return None
        names: List[str] = []
        try:
            for auth in authorships:
                institutions = None
                if isinstance(auth, dict):
                    institutions = auth.get("institutions") or []
                elif hasattr(auth, "institutions"):
                    institutions = auth.institutions or []
                else:
                    institutions = []
                for inst in institutions:
                    if isinstance(inst, dict):
                        name = inst.get("display_name") or inst.get("name")
                    else:
                        name = getattr(inst, "display_name", None) or getattr(inst, "name", None)
                    if name:
                        names.append(name)
            seen = set()
            dedup = []
            for name in names:
                if name not in seen:
                    seen.add(name)
                    dedup.append(name)
            return dedup or None
        except Exception:
            return None

    def _extract_url_from_primary_location(self, primary_location) -> Optional[str]:
        if not primary_location:
            return None
        try:
            if isinstance(primary_location, dict):
                return primary_location.get("landing_page_url")
            if hasattr(primary_location, "landing_page_url"):
                return primary_location.landing_page_url
        except Exception:
            return None
        return None
