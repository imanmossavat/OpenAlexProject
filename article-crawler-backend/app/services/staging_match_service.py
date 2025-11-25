import logging
from typing import Dict, List, Tuple

from ArticleCrawler.api.api_factory import create_api_provider
from ArticleCrawler.pdf_processing.api_matcher import APIMetadataMatcher
from ArticleCrawler.pdf_processing.models import PDFMetadata

from app.schemas.seeds import MatchedSeed
from app.schemas.staging import StagingMatchRow, StagingPaper
from app.services.seed_selection_service import SeedSelectionService
from app.services.staging_identifier_utils import (
    extract_doi_from_url,
    normalize_doi,
    normalize_openalex_id,
)


class StagingMatchService:
    """Resolve staged rows to canonical metadata via provider lookups."""

    def __init__(
        self,
        seed_selection_service: SeedSelectionService,
        logger: logging.Logger,
    ):
        self._seed_selection_service = seed_selection_service
        self._logger = logger

    async def match_rows(
        self,
        *,
        session_id: str,
        rows: List[StagingPaper],
        api_provider: str,
    ) -> List[StagingMatchRow]:
        identifiers: Dict[int, str] = {}
        match_methods: Dict[int, str] = {}
        confidences: Dict[int, float] = {}
        unmatched_reasons: Dict[int, str] = {}

        rows_needing_metadata: List[Tuple[StagingPaper, PDFMetadata]] = []
        candidate_ids: List[str] = []

        for row in rows:
            openalex_id = normalize_openalex_id(row.source_id) or normalize_openalex_id(row.url)
            if openalex_id:
                identifiers[row.staging_id] = openalex_id
                match_methods[row.staging_id] = "source_id"
                candidate_ids.append(openalex_id)
                continue

            doi = (
                normalize_doi(row.doi)
                or normalize_doi(row.source_id)
                or extract_doi_from_url(row.url)
            )
            metadata = None
            if doi or row.title:
                metadata = PDFMetadata(
                    filename=str(row.source_id or row.title or f"staging-{row.staging_id}"),
                    title=row.title or "",
                    doi=doi,
                    year=str(row.year) if row.year is not None else None,
                    authors=row.authors,
                    venue=row.venue,
                )

            if metadata and (metadata.doi or metadata.title):
                rows_needing_metadata.append((row, metadata))
            else:
                unmatched_reasons[row.staging_id] = "Missing DOI or title for matching"

        if rows_needing_metadata:
            api = create_api_provider(api_provider)
            matcher = APIMetadataMatcher(api, logger=self._logger)
            metadata_results = matcher.match_metadata([meta for _, meta in rows_needing_metadata])

            for (row, meta), result in zip(rows_needing_metadata, metadata_results):
                if result.matched and result.paper_id:
                    identifiers[row.staging_id] = result.paper_id
                    match_methods[row.staging_id] = result.match_method or ("doi" if meta.doi else "title_search")
                    confidences[row.staging_id] = result.confidence
                    candidate_ids.append(result.paper_id)
                else:
                    reason = result.match_method or "DOI/title search"
                    unmatched_reasons[row.staging_id] = f"No match found via {reason.lower()}"

        unique_ids = sorted(set(candidate_ids))
        matched_seeds_by_id: Dict[str, MatchedSeed] = {}
        unmatched_errors: Dict[str, str] = {}

        if unique_ids:
            match_result = self._seed_selection_service.match_paper_ids(unique_ids, api_provider)
            matched_seeds_by_id = {seed.paper_id: seed for seed in match_result.matched_seeds}
            unmatched_errors = {item.input_id: item.error for item in match_result.unmatched_seeds}

        match_rows: List[StagingMatchRow] = []
        for row in rows:
            staging_id = row.staging_id
            target_id = identifiers.get(staging_id)

            if target_id and target_id in matched_seeds_by_id:
                seed = matched_seeds_by_id[target_id]
                match_rows.append(
                    StagingMatchRow(
                        staging_id=staging_id,
                        staging=row,
                        matched=True,
                        matched_seed=seed,
                        match_method=match_methods.get(staging_id),
                        confidence=confidences.get(staging_id),
                    )
                )
            else:
                error = unmatched_reasons.get(staging_id)
                if target_id and not error:
                    error = unmatched_errors.get(target_id, "Paper metadata not found in provider")
                match_rows.append(
                    StagingMatchRow(
                        staging_id=staging_id,
                        staging=row,
                        matched=False,
                        match_method=match_methods.get(staging_id),
                        confidence=confidences.get(staging_id),
                        error=error or "Unable to match this paper",
                    )
                )

        return match_rows
