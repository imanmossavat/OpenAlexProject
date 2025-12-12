import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import CrawlerException, InvalidInputException
from app.schemas.staging import RetractionCheckResponse
from app.services.retraction.helpers import (
    RetractionCacheRepository,
    RetractionDOINormalizer,
    RetractionMetadataBuilder,
)
from app.services.staging.retraction_updater import StagingRetractionUpdater
from app.services.staging.service import StagingService


class RetractionWatchService:
    """Run Retraction Watch checks against staged papers."""

    def __init__(
        self,
        logger: logging.Logger,
        staging_service: StagingService,
        retraction_updater: StagingRetractionUpdater,
        cache_dir: Optional[str] = None,
        cache_repository: Optional[RetractionCacheRepository] = None,
        doi_normalizer: Optional[RetractionDOINormalizer] = None,
        metadata_builder: Optional[RetractionMetadataBuilder] = None,
    ) -> None:

        self.logger = logger
        self._staging_service = staging_service
        self._normalizer = doi_normalizer or RetractionDOINormalizer()
        self._cache_repository = cache_repository or RetractionCacheRepository(
            cache_dir=cache_dir,
            logger=logger,
            normalizer=self._normalizer,
        )
        self._metadata_builder = metadata_builder or RetractionMetadataBuilder(self._normalizer)
        self._retraction_updater = retraction_updater

    def check_session(self, session_id: str) -> RetractionCheckResponse:
        rows = self._staging_service.get_all_rows(session_id)
        if not rows:
            raise InvalidInputException("Add some staged papers before running retraction checks.")

        doi_values = []
        for row in rows:
            normalized = self._normalizer.normalize(row.doi)
            if not normalized:
                continue
            doi_values.append(normalized)
        self.logger.info(
            "Retraction check: session=%s total_rows=%d doi_candidates=%d",
            session_id,
            len(rows),
            len(doi_values),
        )

        if not doi_values:
            raise InvalidInputException("No DOIs found. Add DOIs before checking for retractions.")

        manager = self._cache_repository.get_manager()
        try:
            retracted_df, _ = manager.process_retracted_papers(doi_list=doi_values)
        except Exception as exc:  # pragma: no cover - ArticleCrawler handles most errors
            self.logger.error("Failed to run retraction check for session %s: %s", session_id, exc)
            raise CrawlerException("Unable to check retractions right now. Please try again later.") from exc

        retracted_dois = self._metadata_builder.extract_retracted_dois(retracted_df)
        self.logger.debug(
            "Retraction check: session=%s matched_dois=%d sample=%s",
            session_id,
            len(retracted_dois),
            sorted(list(retracted_dois))[:5],
        )
        metadata = self._metadata_builder.build_metadata_map(
            retracted_dois,
            getattr(manager, "retraction_data", None),
        )
        self.logger.debug(
            "Retraction check: metadata entries=%d sample=%s",
            len(metadata),
            list(metadata.items())[:3],
        )
        checked_at = datetime.now(timezone.utc)
        stats = self._retraction_updater.apply(
            session_id,
            retracted_dois=retracted_dois,
            checked_at=checked_at,
            reason="Retraction Watch",
            metadata=metadata,
        )
        self.logger.debug(
            "Retraction check: session=%s eligible=%d retracted=%d skipped_no_doi=%d",
            session_id,
            stats["eligible_rows"],
            stats["retracted_rows"],
            len(rows) - stats["eligible_rows"],
        )

        skipped_without_doi = max(len(rows) - stats["eligible_rows"], 0)
        return RetractionCheckResponse(
            session_id=session_id,
            total_rows=len(rows),
            checked_rows=stats["checked_rows"],
            retracted_count=stats["retracted_rows"],
            skipped_without_doi=skipped_without_doi,
            checked_at=checked_at,
        )

