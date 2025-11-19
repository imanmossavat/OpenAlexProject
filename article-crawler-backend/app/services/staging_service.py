import logging
from math import ceil
from typing import Dict, List, Optional

from app.schemas.staging import (
    StagingListResponse,
    StagingMatchRow,
    StagingPaper,
    StagingPaperCreate,
    StagingPaperUpdate,
)


class StagingService:
    """In-memory staging table manager scoped per session."""

    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 200

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._sessions: Dict[str, Dict] = {}

    def _ensure_session(self, session_id: str) -> Dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "rows": [],
                "next_id": 1,
                "match_rows": [],
            }
        return self._sessions[session_id]

    def _find_row(self, session_id: str, staging_id: int) -> Dict:
        session = self._ensure_session(session_id)
        for row in session["rows"]:
            if row["staging_id"] == staging_id:
                return row
        raise ValueError(f"Staging row {staging_id} not found for session {session_id}")

    def get_row(self, session_id: str, staging_id: int) -> StagingPaper:
        row = self._find_row(session_id, staging_id)
        return StagingPaper(**row)

    def add_rows(self, session_id: str, rows: List[StagingPaperCreate]) -> List[StagingPaper]:
        session = self._ensure_session(session_id)
        created: List[StagingPaper] = []
        existing_keys = self._collect_row_keys(session["rows"])
        for payload in rows:
            key = self._build_row_key_from_payload(payload)
            if key and key in existing_keys:
                self.logger.debug(f"Skipping duplicate staged row for session {session_id} (key: {key})")
                continue
            staging_row = {
                "staging_id": session["next_id"],
                "source": payload.source,
                "source_type": payload.source_type,
                "title": payload.title,
                "authors": payload.authors,
                "year": payload.year,
                "venue": payload.venue,
                "doi": payload.doi,
                "url": payload.url,
                "abstract": payload.abstract,
                "source_id": payload.source_id,
                "is_selected": bool(payload.is_selected),
            }
            session["rows"].append(staging_row)
            created.append(StagingPaper(**staging_row))
            session["next_id"] += 1
            if key:
                existing_keys.add(key)
        self.logger.info(f"Added {len(created)} staged papers to session {session_id}")
        return created

    def update_row(self, session_id: str, staging_id: int, updates: StagingPaperUpdate) -> StagingPaper:
        row = self._find_row(session_id, staging_id)
        for field, value in updates.dict(exclude_unset=True).items():
            row[field] = value
        self.logger.debug(f"Updated staging row {staging_id} for session {session_id}")
        return StagingPaper(**row)

    def set_selection(self, session_id: str, staging_ids: List[int], is_selected: bool) -> int:
        session = self._ensure_session(session_id)
        updated = 0
        target_ids = set(staging_ids)
        for row in session["rows"]:
            if row["staging_id"] in target_ids:
                row["is_selected"] = is_selected
                updated += 1
        self.logger.debug(
            f"Toggled selection for {updated} rows in session {session_id} (selected={is_selected})"
        )
        return updated

    def remove_rows(self, session_id: str, staging_ids: List[int]) -> int:
        session = self._ensure_session(session_id)
        target_ids = set(staging_ids)
        before = len(session["rows"])
        session["rows"] = [row for row in session["rows"] if row["staging_id"] not in target_ids]
        removed = before - len(session["rows"])
        if removed:
            self.logger.info(f"Removed {removed} staged papers from session {session_id}")
        return removed

    def clear_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]
            self.logger.info(f"Cleared staging rows for session {session_id}")
        else:
            self.logger.info(f"Clear staging requested for empty session {session_id}")

    def list_rows(
        self,
        session_id: str,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        source_values: Optional[List[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        title_search: Optional[str] = None,
        venue_search: Optional[str] = None,
        author_search: Optional[str] = None,
        keyword_search: Optional[str] = None,
        doi_presence: Optional[str] = None,
        selected_only: bool = False,
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
    ) -> StagingListResponse:
        session = self._ensure_session(session_id)
        rows = session["rows"]
        selected_count = sum(1 for row in rows if row.get("is_selected"))

        filtered = self._apply_filters(
            rows,
            source_values=source_values,
            year_min=year_min,
            year_max=year_max,
            title_search=title_search,
            venue_search=venue_search,
            author_search=author_search,
            keyword_search=keyword_search,
            doi_presence=doi_presence,
            selected_only=selected_only,
        )

        sorted_rows = self._apply_sort(filtered, sort_by=sort_by, sort_dir=sort_dir)

        size = max(1, min(page_size or self.DEFAULT_PAGE_SIZE, self.MAX_PAGE_SIZE))
        current_page = max(1, page or 1)
        start = (current_page - 1) * size
        end = start + size

        paged_rows = sorted_rows[start:end]
        total_filtered = len(filtered)
        total_pages = ceil(total_filtered / size) if total_filtered else 1

        return StagingListResponse(
            session_id=session_id,
            rows=[StagingPaper(**row) for row in paged_rows],
            total_rows=len(rows),
            filtered_rows=total_filtered,
            selected_count=selected_count,
            page=current_page,
            page_size=size,
            total_pages=total_pages,
        )

    def get_selected_rows(self, session_id: str) -> List[StagingPaper]:
        session = self._ensure_session(session_id)
        return [StagingPaper(**row) for row in session["rows"] if row.get("is_selected")]

    def get_all_rows(self, session_id: str) -> List[StagingPaper]:
        session = self._ensure_session(session_id)
        return [StagingPaper(**row) for row in session["rows"]]

    def store_match_rows(self, session_id: str, rows: List[StagingMatchRow]) -> None:
        session = self._ensure_session(session_id)
        serialized = [
            row.dict()
            if isinstance(row, StagingMatchRow)
            else row
            for row in rows
        ]
        session["match_rows"] = serialized

    def get_match_rows(self, session_id: str) -> List[StagingMatchRow]:
        session = self._ensure_session(session_id)
        stored = session.get("match_rows") or []
        return [
            row
            if isinstance(row, StagingMatchRow)
            else StagingMatchRow(**row)
            for row in stored
        ]

    def _collect_row_keys(self, rows: List[Dict]) -> set:
        keys = set()
        for row in rows:
            key = self._build_row_key_from_dict(row)
            if key:
                keys.add(key)
        return keys

    def _build_row_key_from_payload(self, payload: StagingPaperCreate):
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

    def _build_row_key_from_dict(self, row: Dict):
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


    def _apply_filters(
        self,
        rows: List[Dict],
        *,
        source_values: Optional[List[str]],
        year_min: Optional[int],
        year_max: Optional[int],
        title_search: Optional[str],
        venue_search: Optional[str],
        author_search: Optional[str],
        keyword_search: Optional[str],
        doi_presence: Optional[str],
        selected_only: bool,
    ) -> List[Dict]:
        values = {value.lower() for value in source_values or []}
        title_q = (title_search or "").strip().lower()
        venue_q = (venue_search or "").strip().lower()
        author_q = (author_search or "").strip().lower()
        keyword_q = (keyword_search or "").strip().lower()
        doi_filter = (doi_presence or "").strip().lower()

        filtered = []
        for row in rows:
            if values:
                source = (row.get("source") or "").lower()
                source_type = (row.get("source_type") or "").lower()
                if source not in values and source_type not in values:
                    continue
            year = row.get("year")
            if year_min is not None and year is not None and year < year_min:
                continue
            if year_max is not None and year is not None and year > year_max:
                continue
            if title_q:
                title = (row.get("title") or "").lower()
                if title_q not in title:
                    continue
            if venue_q:
                venue = (row.get("venue") or "").lower()
                if venue_q not in venue:
                    continue
            if author_q:
                authors = (row.get("authors") or "").lower()
                if author_q not in authors:
                    continue
            if keyword_q:
                title = (row.get("title") or "").lower()
                abstract = (row.get("abstract") or "").lower()
                if keyword_q not in title and keyword_q not in abstract:
                    continue
            if doi_filter == "with":
                if not row.get("doi"):
                    continue
            elif doi_filter == "without":
                if row.get("doi"):
                    continue
            if selected_only and not row.get("is_selected"):
                continue
            filtered.append(row)
        return filtered

    def _apply_sort(self, rows: List[Dict], *, sort_by: Optional[str], sort_dir: str) -> List[Dict]:
        if not sort_by:
            return list(rows)

        valid_fields = {
            "title",
            "year",
            "venue",
            "source",
            "source_type",
            "authors",
            "selected",
        }
        if sort_by not in valid_fields:
            return list(rows)

        reverse = (sort_dir or "asc").lower() == "desc"

        sort_field = "is_selected" if sort_by == "selected" else sort_by

        def sort_key(row: Dict):
            value = row.get(sort_field)
            if value is None:
                if sort_field == "year":
                    return -float("inf") if not reverse else float("inf")
                if sort_field == "is_selected":
                    return False
                return ""
            return value

        return sorted(rows, key=sort_key, reverse=reverse)
