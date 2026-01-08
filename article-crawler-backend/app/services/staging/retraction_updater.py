from __future__ import annotations

import logging
from typing import Dict, Optional, Set

from app.services.staging.query_utils import StagingQueryHelper
from app.services.staging.repository import StagingRepository


class StagingRetractionUpdater:
    """Apply retraction metadata to staging sessions."""

    def __init__(
        self,
        repository: Optional[StagingRepository] = None,
        query_helper: Optional[StagingQueryHelper] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self._repository = repository or StagingRepository()
        self._helper = query_helper or StagingQueryHelper()
        self._logger = logger or logging.getLogger(__name__)

    def apply(
        self,
        session_id: str,
        *,
        retracted_dois: Set[str],
        checked_at,
        reason: str,
        metadata: Optional[Dict[str, Dict[str, Optional[str]]]] = None,
    ) -> Dict[str, int]:
        session = self._repository.get_session(session_id)
        normalized = {
            self._helper.normalize_doi(value)
            for value in retracted_dois
            if value and self._helper.normalize_doi(value)
        }
        self._logger.debug(
            "Applying retraction results for session %s with %d matched DOIs",
            session_id,
            len(normalized),
        )
        eligible_rows = 0
        retracted_rows = 0
        metadata = metadata or {}
        for row in session["rows"]:
            doi_value = self._helper.normalize_doi(row.get("doi"))
            self._logger.debug(
                "Row %s DOI normalized to %s (raw=%s)",
                row.get("staging_id"),
                doi_value,
                row.get("doi"),
            )
            if not doi_value:
                row["is_retracted"] = False
                row["retraction_reason"] = None
                row["retraction_checked_at"] = None
                row["retraction_date"] = None
                continue
            eligible_rows += 1
            is_retracted = doi_value in normalized
            if is_retracted:
                self._logger.debug(
                    "Row %s marked retracted (doi=%s)",
                    row.get("staging_id"),
                    doi_value,
                )
            row["is_retracted"] = is_retracted
            info = metadata.get(doi_value)
            row["retraction_reason"] = (info and info.get("reason")) if is_retracted else None
            if row["retraction_reason"] is None and is_retracted:
                row["retraction_reason"] = reason
            row["retraction_date"] = (info and info.get("date")) if is_retracted else None
            row["retraction_checked_at"] = checked_at
            if is_retracted:
                self._logger.debug(
                    "Row %s metadata reason=%r date=%r",
                    row.get("staging_id"),
                    row["retraction_reason"],
                    row["retraction_date"],
                )
                retracted_rows += 1
        self._repository.save_session(session_id, session)
        return {
            "eligible_rows": eligible_rows,
            "retracted_rows": retracted_rows,
            "checked_rows": eligible_rows,
        }
