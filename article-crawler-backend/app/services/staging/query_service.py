from __future__ import annotations

from typing import Dict, List, Optional

from app.schemas.staging import ColumnCustomFilter, StagingListResponse, StagingPaper
from app.services.staging.query_utils import StagingQueryHelper


class StagingQueryService:
    """Compose filtering, sorting, and pagination logic for staging rows."""

    def __init__(self, helper: Optional[StagingQueryHelper] = None):
        self._helper = helper or StagingQueryHelper()

    def list_rows(
        self,
        session_id: str,
        rows: List[Dict],
        *,
        page: int,
        page_size: int,
        sort_by: Optional[str],
        sort_dir: str,
        source_values: Optional[List[str]],
        year_min: Optional[int],
        year_max: Optional[int],
        title_search: Optional[str],
        venue_search: Optional[str],
        author_search: Optional[str],
        keyword_search: Optional[str],
        doi_presence: Optional[str],
        selected_only: bool,
        retraction_status: Optional[str],
        title_values: Optional[List[str]],
        author_values: Optional[List[str]],
        venue_values: Optional[List[str]],
        year_values: Optional[List[int]],
        identifier_filters: Optional[List[Dict[str, str]]],
        custom_filters: Optional[List[ColumnCustomFilter]],
    ) -> StagingListResponse:
        selected_count = sum(1 for row in rows if row.get("is_selected"))
        normalized_identifier_filters = self._helper.normalize_identifier_filters(identifier_filters)
        text_custom_filters, number_custom_filters = self._helper.normalize_custom_filters(custom_filters)

        filtered = self._helper.filter_rows(
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
            retraction_status=retraction_status,
            title_values=title_values,
            author_values=author_values,
            venue_values=venue_values,
            year_values=year_values,
            identifier_filters=normalized_identifier_filters,
            text_custom_filters=text_custom_filters,
            number_custom_filters=number_custom_filters,
        )

        sorted_rows = self._helper.apply_sort(filtered, sort_by=sort_by, sort_dir=sort_dir)

        current_page, size, total_pages = self._helper.paginate(
            len(filtered),
            max(1, page or 1),
            max(1, page_size),
        )
        start = (current_page - 1) * size
        end = start + size
        paged_rows = sorted_rows[start:end]
        selected_column_values = self._helper.accumulate_selected_filters(
            title_values,
            author_values,
            venue_values,
            year_values,
            identifier_filters,
        )
        column_options = self._helper.build_column_options(filtered, selected_column_values)

        return StagingListResponse(
            session_id=session_id,
            rows=[StagingPaper(**row) for row in paged_rows],
            total_rows=len(rows),
            filtered_rows=len(filtered),
            selected_count=selected_count,
            retracted_count=sum(1 for row in rows if row.get("is_retracted")),
            page=current_page,
            page_size=size,
            total_pages=total_pages,
            column_options=column_options,
        )
