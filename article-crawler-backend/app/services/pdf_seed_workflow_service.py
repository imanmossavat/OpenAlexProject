from typing import Dict, List, Optional

import logging

from ArticleCrawler.api.api_factory import create_api_provider
from app.schemas.pdf_seeds import PDFStageResponse, PDFConfirmResponse
from app.schemas.seeds import MatchedSeed
from app.schemas.staging import StagingPaperCreate
from app.services.pdf_seed_service import PDFSeedService
from app.services.seed_session_service import SeedSessionService
from app.services.staging_service import StagingService


class PDFSeedWorkflowService:
    """Coordinate PDF seed upload flows into staging."""

    def __init__(
        self,
        pdf_seed_service: PDFSeedService,
        staging_service: StagingService,
        seed_session_service: SeedSessionService,
        logger: logging.Logger,
    ):
        self._pdf_seed_service = pdf_seed_service
        self._staging_service = staging_service
        self._seed_session_service = seed_session_service
        self._logger = logger

    def stage_reviewed(self, session_id: str, upload_id: str) -> PDFStageResponse:
        """Stage reviewed PDF metadata without matching."""
        self._seed_session_service.get_session(session_id)
        reviewed = self._pdf_seed_service.get_reviewed_metadata(upload_id)
        if not reviewed:
            raise ValueError("No reviewed metadata available. Review metadata before staging.")

        filenames = [md.filename for md in reviewed if getattr(md, "filename", None)]
        stored_files = self._pdf_seed_service.persist_source_files(upload_id, session_id, filenames)
        staging_rows = self._build_staging_rows_from_metadata(reviewed, stored_files)

        added_rows = self._staging_service.add_rows(session_id, staging_rows)
        stats = self._staging_service.list_rows(session_id, page=1, page_size=1)
        self._pdf_seed_service.cleanup_session(upload_id)
        return PDFStageResponse(
            upload_id=upload_id,
            staged_count=len(added_rows),
            total_staged=stats.total_rows,
        )

    def confirm_matches(
        self,
        session_id: str,
        upload_id: str,
        action: str,
    ) -> PDFConfirmResponse:
        """Confirm matched PDF seeds and stage them."""
        self._seed_session_service.get_session(session_id)
        seeds_data = self._pdf_seed_service.get_matched_seeds(upload_id, action)
        matched_seeds = self._build_matched_seeds(seeds_data)
        matched_seeds = self._enrich_seeds(matched_seeds)

        staging_rows = [
            StagingPaperCreate(
                source=seed.source or "Uploaded Files",
                source_type=seed.source_type or "pdf",
                title=seed.title,
                authors=seed.authors,
                year=seed.year,
                venue=seed.venue,
                doi=seed.doi,
                url=seed.url,
                abstract=seed.abstract,
                source_id=seed.source_id or seed.paper_id,
                is_selected=False,
            )
            for seed in matched_seeds
        ]
        staged = self._staging_service.add_rows(session_id, staging_rows) if staging_rows else []
        self._pdf_seed_service.cleanup_session(upload_id)
        stats = self._staging_service.list_rows(session_id, page=1, page_size=1)
        return PDFConfirmResponse(
            upload_id=upload_id,
            added_count=len(staged),
            total_seeds_in_session=stats.total_rows,
        )

    def _build_staging_rows_from_metadata(
        self,
        reviewed_metadata,
        stored_files: Dict[str, str],
    ) -> List[StagingPaperCreate]:
        rows: List[StagingPaperCreate] = []
        for md in reviewed_metadata:
            file_id = stored_files.get(md.filename)
            rows.append(
                StagingPaperCreate(
                    source="Uploaded Files",
                    source_type="pdf",
                    title=md.title,
                    authors=md.authors,
                    year=md.year,
                    venue=md.venue,
                    doi=md.doi,
                    url=None,
                    abstract=md.abstract,
                    source_id=md.doi or md.filename,
                    source_file_id=file_id,
                    source_file_name=md.filename if file_id else None,
                    is_selected=False,
                )
            )
        return rows

    def _build_matched_seeds(self, seeds_data: List[Dict]) -> List[MatchedSeed]:
        matched_seeds: List[MatchedSeed] = []
        for seed in seeds_data or []:
            matched_seeds.append(
                MatchedSeed(
                    paper_id=seed["paper_id"],
                    title=seed["title"],
                    authors=seed["authors"],
                    year=seed["year"],
                    venue=seed["venue"],
                    confidence=seed["confidence"],
                    match_method=seed["match_method"],
                    source="Uploaded Files",
                    source_type="pdf",
                    source_id=seed.get("source_id") or seed["paper_id"],
                )
            )
        return matched_seeds

    def _enrich_seeds(self, seeds: List[MatchedSeed]) -> List[MatchedSeed]:
        """Enrich matched seeds with metadata from OpenAlex."""
        if not seeds:
            return seeds

        try:
            api = create_api_provider("openalex")
        except Exception:
            api = None

        if not api:
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
                extras["cited_by_count"] = (
                    paper.get("cited_by_count")
                    if isinstance(paper.get("cited_by_count"), int)
                    else None
                )
                refs = paper.get("referenced_works")
                extras["references_count"] = len(refs) if isinstance(refs, list) else None
                extras["doi"] = paper.get("doi") or None
                primary_location = paper.get("primary_location") or {}
                extras["url"] = primary_location.get("landing_page_url") if isinstance(primary_location, dict) else None
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
