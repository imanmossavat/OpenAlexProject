from typing import Dict, List, Optional

import logging

from app.schemas.pdf_seeds import PDFStageResponse, PDFConfirmResponse
from app.schemas.seeds import MatchedSeed
from app.schemas.staging import StagingPaperCreate
from app.services.pdf.service import PDFSeedService
from app.services.seeds.session_service import SeedSessionService
from app.services.staging.service import StagingService
from app.services.workflows.pdf_helpers import (
    PDFMatchedSeedBuilder,
    PDFSeedEnricher,
    PDFStagingRowBuilder,
)


class PDFSeedWorkflowService:
    """Coordinate PDF seed upload flows into staging."""

    def __init__(
        self,
        pdf_seed_service: PDFSeedService,
        staging_service: StagingService,
        seed_session_service: SeedSessionService,
        logger: logging.Logger,
        row_builder: Optional[PDFStagingRowBuilder] = None,
        matched_seed_builder: Optional[PDFMatchedSeedBuilder] = None,
        seed_enricher: Optional[PDFSeedEnricher] = None,
    ):
        self._pdf_seed_service = pdf_seed_service
        self._staging_service = staging_service
        self._seed_session_service = seed_session_service
        self._logger = logger
        self._row_builder = row_builder or PDFStagingRowBuilder()
        self._matched_seed_builder = matched_seed_builder or PDFMatchedSeedBuilder()
        self._seed_enricher = seed_enricher or PDFSeedEnricher(logger)

    def stage_reviewed(self, session_id: str, upload_id: str) -> PDFStageResponse:
        """Stage reviewed PDF metadata without matching."""
        self._seed_session_service.get_session(session_id)
        reviewed = self._pdf_seed_service.get_reviewed_metadata(upload_id)
        if not reviewed:
            raise ValueError("No reviewed metadata available. Review metadata before staging.")

        filenames = [md.filename for md in reviewed if getattr(md, "filename", None)]
        stored_files = self._pdf_seed_service.persist_source_files(upload_id, session_id, filenames)
        staging_rows = self._row_builder.build_from_reviewed(reviewed, stored_files)

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
        matched_seeds = self._matched_seed_builder.build(seeds_data)
        matched_seeds = self._seed_enricher.enrich(matched_seeds)

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

