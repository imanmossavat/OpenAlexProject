import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Set

import pandas as pd

from ArticleCrawler.config.retraction_config import RetractionConfig
from ArticleCrawler.config.storage_config import StorageAndLoggingConfig
from ArticleCrawler.papervalidation.retraction_watch_manager import RetractionWatchManager

from app.core.exceptions import CrawlerException, InvalidInputException
from app.schemas.staging import RetractionCheckResponse
from app.services.staging_service import StagingService


class RetractionWatchService:
    """Run Retraction Watch checks against staged papers."""

    def __init__(
        self,
        logger: logging.Logger,
        staging_service: StagingService,
        cache_dir: Optional[str] = None,
    ) -> None:
        self.logger = logger
        self._staging_service = staging_service
        self._cache_dir = Path(cache_dir or "retraction_cache").resolve()
        self._manager: Optional[RetractionWatchManager] = None

    def check_session(self, session_id: str) -> RetractionCheckResponse:
        rows = self._staging_service.get_all_rows(session_id)
        if not rows:
            raise InvalidInputException("Add some staged papers before running retraction checks.")

        doi_values = []
        for row in rows:
            normalized = self._normalize_doi(row.doi)
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

        manager = self._get_manager()
        try:
            retracted_df, _ = manager.process_retracted_papers(doi_list=doi_values)
        except Exception as exc:  # pragma: no cover - ArticleCrawler handles most errors
            self.logger.error("Failed to run retraction check for session %s: %s", session_id, exc)
            raise CrawlerException("Unable to check retractions right now. Please try again later.") from exc

        retracted_dois = self._extract_retracted_dois(retracted_df)
        self.logger.debug(
            "Retraction check: session=%s matched_dois=%d sample=%s",
            session_id,
            len(retracted_dois),
            sorted(list(retracted_dois))[:5],
        )
        metadata = self._build_metadata_map(retracted_dois)
        self.logger.debug(
            "Retraction check: metadata entries=%d sample=%s",
            len(metadata),
            list(metadata.items())[:3],
        )
        checked_at = datetime.now(timezone.utc)
        stats = self._staging_service.apply_retraction_results(
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

    def _get_manager(self) -> RetractionWatchManager:
        if self._manager is None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            storage_config = StorageAndLoggingConfig(
                experiment_file_name="retraction_watch_cache",
                root_folder=self._cache_dir,
            )
            retraction_config = RetractionConfig(enable_retraction_watch=True)
            manager = RetractionWatchManager(
                storage_and_logging_options=storage_config,
                retraction_options=retraction_config,
                logger=self.logger,
            )
            retraction_data = getattr(manager, "retraction_data", None)
            if retraction_data is not None:
                manager.retraction_data = self._normalize_retraction_frame(retraction_data)
            self._manager = manager
        return self._manager

    @staticmethod
    def _normalize_doi(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        normalized = str(value).strip().lower()
        prefixes = ("https://doi.org/", "http://doi.org/", "http://dx.doi.org/", "https://dx.doi.org/", "doi:")
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        normalized = normalized.strip()
        return normalized or None

    def _extract_retracted_dois(self, retracted_df) -> Set[str]:
        if retracted_df is None or getattr(retracted_df, "empty", True):
            return set()
        values: Set[str] = set()
        try:
            for raw in retracted_df.get("doi", []):
                normalized = self._normalize_doi(str(raw))
                if normalized:
                    values.add(normalized)
        except Exception:
            pass
        return values

    def _build_metadata_map(self, retracted_dois: Set[str]) -> Dict[str, Dict[str, Optional[str]]]:
        """Return metadata for matched DOIs pulled from Retraction Watch data."""
        metadata: Dict[str, Dict[str, Optional[str]]] = {}
        source = getattr(self._manager, "retraction_data", None)
        if source is None or not hasattr(source, "iterrows") or not retracted_dois:
            return metadata
        try:
            doi_mask = False
            for column in ("RetractionDOI", "OriginalPaperDOI"):
                if column not in source.columns:
                    continue
                doi_mask = doi_mask | source[column].isin(retracted_dois)
            subset = source[doi_mask] if doi_mask is not False else source.iloc[0:0]
            for _, row in subset.iterrows():
                reason = row.get("Reason") or row.get("RetractionNature")
                date = row.get("RetractionDate")
                original = self._normalize_doi(row.get("OriginalPaperDOI"))
                retraction = self._normalize_doi(row.get("RetractionDOI"))
                payload = {"reason": reason, "date": date}
                if original and original not in metadata:
                    metadata[original] = payload
                    self.logger.debug(
                        "Metadata mapped for original DOI %s reason=%r date=%r",
                        original,
                        reason,
                        date,
                    )
                if retraction and retraction not in metadata:
                    metadata[retraction] = payload
                    self.logger.debug(
                        "Metadata mapped for retraction DOI %s reason=%r date=%r",
                        retraction,
                        reason,
                        date,
                    )
        except Exception as exc:  # pragma: no cover
            self.logger.warning("Unable to build metadata map: %s", exc)
        return metadata

    def _normalize_retraction_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized = df.copy()
        doi_columns = ["RetractionDOI", "OriginalPaperDOI"]
        for column in doi_columns:
            if column not in normalized.columns:
                continue
            normalized[column] = normalized[column].apply(self._normalize_doi)
        return normalized
