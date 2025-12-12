from typing import List, Optional

from fastapi import HTTPException

from app.schemas.seed_session import AddSeedsToSessionResponse
from app.schemas.staging import (
    BulkRemoveRequest,
    BulkRemoveResponse,
    MatchSelectedRequest,
    SelectionUpdateRequest,
    SelectionUpdateResponse,
    StagingListResponse,
    StagingMatchResponse,
    StagingMatchRow,
    StagingPaper,
    StagingPaperCreate,
)


class StagingRouteHelper:
    """Aggregate staging-related route orchestration logic."""

    def __init__(
        self,
        staging_service,
        query_parser,
        manual_metadata_enricher,
        match_service,
        seed_session_service,
    ):
        self.staging_service = staging_service
        self.query_parser = query_parser
        self.manual_metadata_enricher = manual_metadata_enricher
        self.match_service = match_service
        self.seed_session_service = seed_session_service

    def list_staged_papers(
        self,
        session_id: str,
        *,
        page: int,
        page_size: int,
        sources: Optional[List[str]],
        year_min: Optional[int],
        year_max: Optional[int],
        title: Optional[str],
        venue: Optional[str],
        author: Optional[str],
        keyword: Optional[str],
        doi_presence: Optional[str],
        retraction_status: Optional[str],
        title_values: Optional[List[str]],
        author_values: Optional[List[str]],
        venue_values: Optional[List[str]],
        year_values: Optional[List[int]],
        identifier_values: Optional[List[str]],
        column_filters: Optional[List[str]],
        selected_only: bool,
        sort_by: Optional[str],
        sort_dir: str,
    ) -> StagingListResponse:
        identifier_filters = self.query_parser.parse_identifier_filters(identifier_values)
        custom_filters = self.query_parser.parse_column_filters(column_filters)

        try:
            self.query_parser.validate_retraction_status(retraction_status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return self.staging_service.list_rows(
            session_id,
            page=page,
            page_size=page_size,
            source_values=sources,
            year_min=year_min,
            year_max=year_max,
            title_search=title,
            venue_search=venue,
            author_search=author,
            keyword_search=keyword,
            doi_presence=doi_presence,
            title_values=title_values,
            author_values=author_values,
            venue_values=venue_values,
            year_values=year_values,
            identifier_filters=identifier_filters,
            custom_filters=custom_filters,
            selected_only=selected_only,
            retraction_status=retraction_status,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    async def add_staged_papers(
        self,
        session_id: str,
        payload: List[StagingPaperCreate],
    ) -> List[StagingPaper]:
        rows_to_add, invalid_manual_ids = await self.manual_metadata_enricher.enrich(payload)
        if not rows_to_add:
            detail = "No rows to add."
            if invalid_manual_ids:
                detail = "No valid manual IDs were found."
            raise HTTPException(status_code=400, detail=detail)

        if invalid_manual_ids:
            self.staging_service.logger.warning(
                "Skipping %d invalid manual IDs when staging: %s",
                len(invalid_manual_ids),
                ", ".join(invalid_manual_ids[:5]) + ("..." if len(invalid_manual_ids) > 5 else ""),
            )
        return self.staging_service.add_rows(session_id, rows_to_add)

    def update_selection(self, session_id: str, request: SelectionUpdateRequest) -> SelectionUpdateResponse:
        updated = self.staging_service.set_selection(session_id, request.staging_ids, request.is_selected)
        stats = self.staging_service.list_rows(session_id, page=1, page_size=1)
        return SelectionUpdateResponse(updated_count=updated, selected_count=stats.selected_count)

    async def match_selected_rows(
        self,
        session_id: str,
        payload: MatchSelectedRequest,
    ) -> StagingMatchResponse:
        selected_rows = self.staging_service.get_selected_rows(session_id)
        if not selected_rows:
            raise HTTPException(status_code=400, detail="No selected staged papers to match")

        match_rows = await self.match_service.match_rows(
            session_id=session_id,
            rows=selected_rows,
            api_provider=payload.api_provider,
        )
        self.staging_service.store_match_rows(session_id, match_rows)

        matched_rows = [row for row in match_rows if row.matched]
        unmatched_rows = [row for row in match_rows if not row.matched]
        return StagingMatchResponse(
            session_id=session_id,
            total_selected=len(selected_rows),
            matched_rows=matched_rows,
            unmatched_rows=unmatched_rows,
        )

    def get_last_match_results(self, session_id: str) -> StagingMatchResponse:
        rows = self.staging_service.get_match_rows(session_id)
        if not rows:
            raise HTTPException(status_code=404, detail="No match results stored for this session")
        matched_rows = [row for row in rows if row.matched]
        unmatched_rows = [row for row in rows if not row.matched]
        return StagingMatchResponse(
            session_id=session_id,
            total_selected=len(rows),
            matched_rows=matched_rows,
            unmatched_rows=unmatched_rows,
        )

    def confirm_matches(self, session_id: str, staging_ids: Optional[List[int]]) -> AddSeedsToSessionResponse:
        rows = self.staging_service.get_match_rows(session_id)
        if not rows:
            raise HTTPException(status_code=400, detail="Match results not found. Run matching first.")

        allowed_ids = set(staging_ids) if staging_ids else None
        seeds = [
            row.matched_seed
            for row in rows
            if row.matched and row.matched_seed and (allowed_ids is None or row.staging_id in allowed_ids)
        ]
        if not seeds:
            raise HTTPException(status_code=400, detail="No matched seeds to confirm.")

        return self.seed_session_service.set_seeds_for_session(session_id, seeds)

    async def rematch_single_row(
        self,
        session_id: str,
        staging_id: int,
        payload: MatchSelectedRequest,
    ) -> StagingMatchRow:
        row = self.staging_service.get_row(session_id, staging_id)
        match_rows = await self.match_service.match_rows(
            session_id=session_id,
            rows=[row],
            api_provider=payload.api_provider,
        )
        if not match_rows:
            raise HTTPException(status_code=400, detail="Unable to match this paper")
        new_row = match_rows[0]
        existing = self.staging_service.get_match_rows(session_id)
        for idx, existing_row in enumerate(existing):
            if existing_row.staging_id == staging_id:
                existing[idx] = new_row
                break
        else:
            existing.append(new_row)
        self.staging_service.store_match_rows(session_id, existing)
        return new_row

    def remove_staged_papers(
        self,
        session_id: str,
        request: BulkRemoveRequest,
    ) -> BulkRemoveResponse:
        removed = self.staging_service.remove_rows(session_id, request.staging_ids)
        stats = self.staging_service.list_rows(session_id, page=1, page_size=1)
        return BulkRemoveResponse(removed_count=removed, total_rows=stats.total_rows)

    def remove_single_paper(self, session_id: str, staging_id: int) -> BulkRemoveResponse:
        removed = self.staging_service.remove_rows(session_id, [staging_id])
        stats = self.staging_service.list_rows(session_id, page=1, page_size=1)
        return BulkRemoveResponse(removed_count=removed, total_rows=stats.total_rows)
