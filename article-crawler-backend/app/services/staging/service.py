import logging
from typing import Dict, List, Optional

from app.schemas.staging import (
    ColumnCustomFilter,
    StagingListResponse,
    StagingMatchRow,
    StagingPaper,
    StagingPaperCreate,
    StagingPaperUpdate,
)
from app.services.staging.query_service import StagingQueryService
from app.services.staging.query_utils import StagingQueryHelper
from app.services.staging.repository import StagingRepository
from app.services.staging.retraction_updater import StagingRetractionUpdater
from app.services.staging.row_manager import StagingRowManager
from app.services.staging.session_store import StagingSessionStore


class StagingService:
    """In-memory staging table manager scoped per session."""

    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 200

    def __init__(
        self,
        logger: logging.Logger,
        repository: Optional[StagingRepository] = None,
        session_store: Optional[StagingSessionStore] = None,
        query_service: Optional[StagingQueryService] = None,
        query_helper: Optional[StagingQueryHelper] = None,
        retraction_updater: Optional[StagingRetractionUpdater] = None,
        row_manager: Optional[StagingRowManager] = None,
    ):
        self.logger = logger
        self._repository = repository or StagingRepository(session_store=session_store)
        helper = query_helper or StagingQueryHelper()
        self._query_service = query_service or StagingQueryService(helper)
        self._retraction_updater = retraction_updater or StagingRetractionUpdater(
            repository=self._repository,
            query_helper=helper,
            logger=logger,
        )
        self._row_manager = row_manager or StagingRowManager(logger=logger)

    def get_row(self, session_id: str, staging_id: int) -> StagingPaper:
        session = self._repository.get_session(session_id)
        return self._row_manager.get_row(session, staging_id)

    def add_rows(self, session_id: str, rows: List[StagingPaperCreate]) -> List[StagingPaper]:
        session = self._repository.get_session(session_id)
        created = self._row_manager.add_rows(session, rows)
        if created:
            self._repository.save_session(session_id, session)
        return created

    def update_row(self, session_id: str, staging_id: int, updates: StagingPaperUpdate) -> StagingPaper:
        session = self._repository.get_session(session_id)
        updated = self._row_manager.update_row(session, staging_id, updates)
        self._repository.save_session(session_id, session)
        return updated

    def set_selection(self, session_id: str, staging_ids: List[int], is_selected: bool) -> int:
        session = self._repository.get_session(session_id)
        updated = self._row_manager.set_selection(session, staging_ids, is_selected)
        if updated:
            self._repository.save_session(session_id, session)
        return updated

    def remove_rows(self, session_id: str, staging_ids: List[int]) -> int:
        session = self._repository.get_session(session_id)
        removed = self._row_manager.remove_rows(session, staging_ids)
        if removed:
            self._repository.save_session(session_id, session)
        return removed

    def clear_session(self, session_id: str) -> None:
        session = self._repository.get_session(session_id)
        if session.get("rows") or session.get("match_rows"):
            self._repository.delete_session(session_id)
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
        retraction_status: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
        title_values: Optional[List[str]] = None,
        author_values: Optional[List[str]] = None,
        venue_values: Optional[List[str]] = None,
        year_values: Optional[List[int]] = None,
        identifier_filters: Optional[List[Dict[str, str]]] = None,
        custom_filters: Optional[List[ColumnCustomFilter]] = None,
    ) -> StagingListResponse:
        session = self._repository.get_session(session_id)
        rows = session["rows"]
        requested_size = page_size or self.DEFAULT_PAGE_SIZE
        limited_size = max(1, min(requested_size, self.MAX_PAGE_SIZE))
        requested_page = max(1, page or 1)

        return self._query_service.list_rows(
            session_id,
            rows,
            page=requested_page,
            page_size=limited_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            source_values=source_values,
            year_min=year_min,
            year_max=year_max,
            title_search=title_search,
            venue_search=venue_search,
            author_search=author_search,
            keyword_search=keyword_search,
            doi_presence=doi_presence,
            selected_only=selected_only,
            retraction_status=retraction_status,
            title_values=title_values,
            author_values=author_values,
            venue_values=venue_values,
            year_values=year_values,
            identifier_filters=identifier_filters,
            custom_filters=custom_filters,
        )

    def apply_retraction_results(
        self,
        session_id: str,
        *,
        retracted_dois: set,
        checked_at,
        reason: str,
        metadata: Optional[Dict[str, Dict[str, Optional[str]]]] = None,
    ) -> Dict[str, int]:
        return self._retraction_updater.apply(
            session_id,
            retracted_dois=retracted_dois,
            checked_at=checked_at,
            reason=reason,
            metadata=metadata,
        )

    def get_selected_rows(self, session_id: str) -> List[StagingPaper]:
        session = self._repository.get_session(session_id)
        return [StagingPaper(**row) for row in session["rows"] if row.get("is_selected")]

    def get_all_rows(self, session_id: str) -> List[StagingPaper]:
        session = self._repository.get_session(session_id)
        return [StagingPaper(**row) for row in session["rows"]]

    def store_match_rows(self, session_id: str, rows: List[StagingMatchRow]) -> None:
        session = self._repository.get_session(session_id)
        self._row_manager.store_match_rows(session, rows)
        self._repository.save_session(session_id, session)

    def get_match_rows(self, session_id: str) -> List[StagingMatchRow]:
        session = self._repository.get_session(session_id)
        stored = session.get("match_rows") or []
        return [
            row
            if isinstance(row, StagingMatchRow)
            else StagingMatchRow(**row)
            for row in stored
        ]

