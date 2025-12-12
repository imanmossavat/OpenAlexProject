from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from app.schemas.staging import (
    StagingMatchRow,
    StagingPaper,
    StagingPaperCreate,
    StagingPaperUpdate,
    _normalize_venue_value,
)


class StagingRowManager:
    """Encapsulate row-level operations for staging sessions."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    def add_rows(self, session: Dict, rows: Sequence[StagingPaperCreate]) -> List[StagingPaper]:
        created: List[StagingPaper] = []
        existing_keys = self._collect_row_keys(session.get("rows", []))
        for payload in rows or []:
            key = self._build_row_key_from_payload(payload)
            if key and key in existing_keys:
                self._logger.debug("Skipping duplicate staged row (key=%s)", key)
                continue
            staging_row = self._build_row_dict(session, payload)
            session.setdefault("rows", []).append(staging_row)
            created.append(StagingPaper(**staging_row))
            session["next_id"] = session.get("next_id", 1) + 1
            if key:
                existing_keys.add(key)
        if created:
            self._logger.info("Added %s staged papers", len(created))
        return created

    def get_row(self, session: Dict, staging_id: int) -> StagingPaper:
        row = self._find_row(session, staging_id)
        return StagingPaper(**row)

    def update_row(
        self,
        session: Dict,
        staging_id: int,
        updates: StagingPaperUpdate,
    ) -> StagingPaper:
        row = self._find_row(session, staging_id)
        payload = updates.dict(exclude_unset=True)
        for field, value in payload.items():
            if field == "venue":
                row[field] = _normalize_venue_value(value)
            else:
                row[field] = value
        if "doi" in payload:
            row["is_retracted"] = False
            row["retraction_reason"] = None
            row["retraction_checked_at"] = None
            row["retraction_date"] = None
        self._logger.debug("Updated staging row %s", staging_id)
        return StagingPaper(**row)

    def set_selection(self, session: Dict, staging_ids: Iterable[int], is_selected: bool) -> int:
        updated = 0
        target_ids = set(staging_ids or [])
        for row in session.get("rows", []):
            if row.get("staging_id") in target_ids:
                row["is_selected"] = is_selected
                updated += 1
        if updated:
            self._logger.debug("Toggled selection for %s rows (selected=%s)", updated, is_selected)
        return updated

    def remove_rows(self, session: Dict, staging_ids: Iterable[int]) -> int:
        target_ids = set(staging_ids or [])
        rows = session.get("rows", [])
        before = len(rows)
        session["rows"] = [row for row in rows if row.get("staging_id") not in target_ids]
        removed = before - len(session["rows"])
        if removed:
            self._logger.info("Removed %s staged papers", removed)
        return removed

    def store_match_rows(self, session: Dict, rows: List[Union[StagingMatchRow, Dict]]) -> None:
        serialized = [
            row.dict() if isinstance(row, StagingMatchRow) else row
            for row in rows or []
        ]
        session["match_rows"] = serialized

    def _build_row_dict(self, session: Dict, payload: StagingPaperCreate) -> Dict:
        normalized_venue = _normalize_venue_value(payload.venue)
        return {
            "staging_id": session.get("next_id", 1),
            "source": payload.source,
            "source_type": payload.source_type,
            "is_library_seed": bool(payload.is_library_seed),
            "title": payload.title,
            "authors": payload.authors,
            "year": payload.year,
            "venue": normalized_venue,
            "doi": payload.doi,
            "url": payload.url,
            "abstract": payload.abstract,
            "is_retracted": bool(payload.is_retracted),
            "retraction_reason": payload.retraction_reason,
            "retraction_checked_at": payload.retraction_checked_at,
            "retraction_date": payload.retraction_date,
            "source_id": payload.source_id,
            "is_selected": bool(payload.is_selected),
            "source_file_id": payload.source_file_id,
            "source_file_name": payload.source_file_name,
        }

    def _find_row(self, session: Dict, staging_id: int) -> Dict:
        for row in session.get("rows", []):
            if row.get("staging_id") == staging_id:
                return row
        raise ValueError(f"Staging row {staging_id} not found")

    def _collect_row_keys(self, rows: List[Dict]) -> set:
        keys = set()
        for row in rows:
            key = self._build_row_key_from_dict(row)
            if key:
                keys.add(key)
        return keys

    def _build_row_key_from_payload(self, payload: StagingPaperCreate) -> Optional[Tuple]:
        doi = (payload.doi or "").strip().lower()
        if doi:
            return ("doi", doi)
        source_id = (payload.source_id or "").strip().lower()
        if source_id:
            source_type = (payload.source_type or "").strip().lower()
            return ("source_id", source_type, source_id)
        title = (payload.title or "").strip().lower()
        year = payload.year or None
        if title:
            return ("title_year", title, year)
        return None

    def _build_row_key_from_dict(self, row: Dict) -> Optional[Tuple]:
        doi = (row.get("doi") or "").strip().lower()
        if doi:
            return ("doi", doi)
        source_id = (row.get("source_id") or "").strip().lower()
        if source_id:
            source_type = (row.get("source_type") or "").strip().lower()
            return ("source_id", source_type, source_id)
        title = (row.get("title") or "").strip().lower()
        year = row.get("year") or None
        if title:
            return ("title_year", title, year)
        return None
