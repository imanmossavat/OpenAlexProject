from typing import List, Tuple

from app.schemas.staging import StagingPaperCreate
from app.services.seed_selection_service import SeedSelectionService
from app.services.staging_identifier_utils import normalize_openalex_id


class ManualMetadataEnricher:
    """Enriches manually staged rows with metadata fetched from providers."""

    def __init__(self, seed_selection_service: SeedSelectionService):
        self._seed_selection_service = seed_selection_service

    async def enrich(
        self, rows: List[StagingPaperCreate]
    ) -> Tuple[List[StagingPaperCreate], List[str]]:
        enriched_rows: List[StagingPaperCreate] = []
        invalid_manual_ids: List[str] = []

        for row in rows or []:
            if row.source_type != "manual":
                enriched_rows.append(row)
                continue

            label = (row.source or "").strip()
            if not label or label.lower() in {"manual", "manual ids", "manual id", "manual papers"}:
                label = "Manual IDs"
            row.source = label

            identifier = row.doi or row.source_id or row.url
            identifier_for_error = identifier or row.source_id or "unknown"

            if not identifier:
                invalid_manual_ids.append(str(identifier_for_error))
                continue

            try:
                match_result = self._seed_selection_service.match_paper_ids(
                    [identifier], api_provider="openalex"
                )
            except Exception:
                invalid_manual_ids.append(str(identifier_for_error))
                continue

            if not match_result.matched_seeds:
                invalid_manual_ids.append(str(identifier_for_error))
                continue

            seed = match_result.matched_seeds[0]
            row.title = row.title or seed.title
            row.authors = row.authors or seed.authors
            row.year = row.year or seed.year
            row.venue = row.venue or seed.venue
            row.doi = row.doi or seed.doi
            row.url = row.url or seed.url
            row.abstract = row.abstract or seed.abstract
            if seed.paper_id and not normalize_openalex_id(row.source_id or ""):
                row.source_id = seed.paper_id

            enriched_rows.append(row)

        return enriched_rows, invalid_manual_ids
