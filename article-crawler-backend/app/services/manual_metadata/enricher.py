from typing import List, Optional, Tuple

from app.schemas.staging import StagingPaperCreate
from app.services.manual_metadata.helpers import (
    ManualMetadataLookup,
    ManualMetadataMerger,
    ManualMetadataRepository,
)
from app.services.seeds.selection_service import SeedSelectionService


class ManualMetadataEnricher:
    """Enriches manually staged rows with metadata fetched from providers."""

    def __init__(
        self,
        seed_selection_service: SeedSelectionService,
        repository: Optional[ManualMetadataRepository] = None,
        lookup_helper: Optional[ManualMetadataLookup] = None,
        merger: Optional[ManualMetadataMerger] = None,
    ):
        self._repository = repository or ManualMetadataRepository()
        self._lookup = lookup_helper or ManualMetadataLookup(seed_selection_service)
        self._merger = merger or ManualMetadataMerger()

    async def enrich(
        self, rows: List[StagingPaperCreate]
    ) -> Tuple[List[StagingPaperCreate], List[str]]:
        enriched_rows: List[StagingPaperCreate] = []
        invalid_manual_ids: List[str] = []

        for row in rows or []:
            if not self._repository.is_manual(row):
                enriched_rows.append(row)
                continue

            self._repository.normalize_source_label(row)
            identifier = self._repository.extract_identifier(row)
            identifier_for_error = identifier or row.source_id or "unknown"

            if not identifier:
                invalid_manual_ids.append(str(identifier_for_error))
                continue

            try:
                seed = self._lookup.lookup(identifier)
            except Exception:
                seed = None

            if not seed:
                invalid_manual_ids.append(str(identifier_for_error))
                continue

            self._merger.merge(row, seed)
            enriched_rows.append(row)

        return enriched_rows, invalid_manual_ids
