from __future__ import annotations

from typing import Optional

from app.schemas.seeds import MatchedSeed
from app.schemas.staging import StagingPaperCreate
from app.services.seeds.selection_service import SeedSelectionService
from app.services.staging.identifier_utils import normalize_openalex_id


class ManualMetadataRepository:
    """Utility repository for interacting with manual metadata rows."""

    def is_manual(self, row: StagingPaperCreate) -> bool:
        return (row.source_type or "").lower() == "manual"

    def normalize_source_label(self, row: StagingPaperCreate) -> None:
        label = (row.source or "").strip()
        if not label or label.lower() in {"manual", "manual ids", "manual id", "manual papers"}:
            label = "Manual IDs"
        row.source = label

    def extract_identifier(self, row: StagingPaperCreate) -> Optional[str]:
        return row.doi or row.source_id or row.url


class ManualMetadataLookup:
    """Perform API lookups for manual identifiers."""

    def __init__(self, seed_selection_service: SeedSelectionService):
        self._seed_selection_service = seed_selection_service

    def lookup(self, identifier: str) -> Optional[MatchedSeed]:
        match_result = self._seed_selection_service.match_paper_ids(
            [identifier],
            api_provider="openalex",
        )
        if not match_result or not match_result.matched_seeds:
            return None
        return match_result.matched_seeds[0]


class ManualMetadataMerger:
    """Merge fetched metadata onto staging rows."""

    def merge(self, row: StagingPaperCreate, seed: MatchedSeed) -> None:
        row.title = row.title or seed.title
        row.authors = row.authors or seed.authors
        row.year = row.year or seed.year
        row.venue = row.venue or seed.venue
        row.doi = row.doi or seed.doi
        row.url = row.url or seed.url
        row.abstract = row.abstract or seed.abstract
        if seed.paper_id and not normalize_openalex_id(row.source_id or ""):
            row.source_id = seed.paper_id
