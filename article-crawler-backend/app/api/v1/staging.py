from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import FileResponse
import mimetypes

from app.api.dependencies import (
    get_manual_metadata_enricher,
    get_retraction_service,
    get_seed_session_service,
    get_source_file_service,
    get_staging_match_service,
    get_staging_query_parser,
    get_staging_service,
)
from app.schemas.seed_session import AddSeedsToSessionResponse
from app.schemas.staging import (
    BulkRemoveRequest,
    BulkRemoveResponse,
    ConfirmMatchesRequest,
    MatchSelectedRequest,
    SelectionUpdateRequest,
    SelectionUpdateResponse,
    StagingListResponse,
    StagingMatchResponse,
    StagingMatchRow,
    StagingPaper,
    StagingPaperCreate,
    StagingPaperUpdate,
    RetractionCheckResponse,
)

router = APIRouter()


@router.get(
    "/seeds/session/{session_id}/staging",
    response_model=StagingListResponse,
)
async def list_staged_papers(
    session_id: str = Path(..., description="Seed session identifier"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sources: Optional[List[str]] = Query(None, description="Filter by source labels/source types"),
    year_min: Optional[int] = Query(None, description="Minimum publication year"),
    year_max: Optional[int] = Query(None, description="Maximum publication year"),
    title: Optional[str] = Query(None, description="Title search query"),
    venue: Optional[str] = Query(None, description="Venue search query"),
    author: Optional[str] = Query(None, description="Author search query"),
    keyword: Optional[str] = Query(None, description="Keyword search across title and abstract"),
    doi_presence: Optional[str] = Query(
        None,
        description="Filter by DOI presence: 'with' for rows with DOI, 'without' for rows without DOI",
    ),
    retraction_status: Optional[str] = Query(
        None,
        description="Filter rows that are 'retracted' or 'not_retracted'",
    ),
    title_values: Optional[List[str]] = Query(None, description="Exact match filters for the title column"),
    author_values: Optional[List[str]] = Query(None, description="Exact match filters for the authors column"),
    venue_values: Optional[List[str]] = Query(None, description="Exact match filters for the venue column"),
    year_values: Optional[List[int]] = Query(None, description="Exact match filters for publication year"),
    identifier_values: Optional[List[str]] = Query(
        None,
        description="Identifier filters using 'field::value' format (e.g., 'doi::10.1234/foo')",
    ),
    column_filters: Optional[List[str]] = Query(
        None,
        description="Advanced column filters in the form column::operator::value(::value_to)",
    ),
    selected_only: bool = Query(False, description="Return only selected rows"),
    sort_by: Optional[str] = Query(None, description="Sort column"),
    sort_dir: str = Query("asc", description="Sort direction asc|desc"),
    query_parser=Depends(get_staging_query_parser),
    service=Depends(get_staging_service),
):
    """Return paginated staged papers for a session."""
    identifier_filters = query_parser.parse_identifier_filters(identifier_values)
    custom_filters = query_parser.parse_column_filters(column_filters)

    try:
        query_parser.validate_retraction_status(retraction_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return service.list_rows(
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


@router.post(
    "/seeds/session/{session_id}/staging/retractions/check",
    response_model=RetractionCheckResponse,
)
async def check_retractions(
    session_id: str,
    service=Depends(get_retraction_service),
):
    """Trigger a Retraction Watch check for all staged papers in a session."""
    return service.check_session(session_id)


@router.post(
    "/seeds/session/{session_id}/staging",
    response_model=List[StagingPaper],
)
async def add_staged_papers(
    session_id: str,
    payload: List[StagingPaperCreate],
    staging_service=Depends(get_staging_service),
    manual_metadata_enricher=Depends(get_manual_metadata_enricher),
):
    """Add papers to the staging table."""
    rows_to_add, invalid_manual_ids = await manual_metadata_enricher.enrich(payload)
    if not rows_to_add:
        detail = (
            "No valid manual IDs were found."
            if invalid_manual_ids
            else "No rows to add."
        )
        raise HTTPException(status_code=400, detail=detail)
    if invalid_manual_ids:
        staging_service.logger.warning(
            "Skipping %d invalid manual IDs when staging: %s",
            len(invalid_manual_ids),
            ", ".join(invalid_manual_ids[:5]) + ("..." if len(invalid_manual_ids) > 5 else ""),
        )
    return staging_service.add_rows(session_id, rows_to_add)


@router.patch(
    "/seeds/session/{session_id}/staging/{staging_id}",
    response_model=StagingPaper,
)
async def update_staged_paper(
    session_id: str,
    staging_id: int,
    payload: StagingPaperUpdate,
    service=Depends(get_staging_service),
):
    """Inline edit for staged paper row."""
    return service.update_row(session_id, staging_id, payload)


@router.post(
    "/seeds/session/{session_id}/staging/select",
    response_model=SelectionUpdateResponse,
)
async def update_selection(
    session_id: str,
    payload: SelectionUpdateRequest,
    service=Depends(get_staging_service),
):
    """Toggle selection for multiple staged papers."""
    updated = service.set_selection(session_id, payload.staging_ids, payload.is_selected)
    stats = service.list_rows(session_id, page=1, page_size=1)
    return SelectionUpdateResponse(updated_count=updated, selected_count=stats.selected_count)


@router.post(
    "/seeds/session/{session_id}/staging/match",
    response_model=StagingMatchResponse,
)
async def match_selected_rows(
    session_id: str,
    payload: MatchSelectedRequest,
    staging_service=Depends(get_staging_service),
    match_service=Depends(get_staging_match_service),
):
    """Match currently selected staged rows using DOI/title heuristics."""
    try:
        selected_rows = staging_service.get_selected_rows(session_id)
        if not selected_rows:
            raise HTTPException(status_code=400, detail="No selected staged papers to match")

        match_rows = await match_service.match_rows(
            session_id=session_id,
            rows=selected_rows,
            api_provider=payload.api_provider,
        )

        staging_service.store_match_rows(session_id, match_rows)

        matched_rows = [row for row in match_rows if row.matched]
        unmatched_rows = [row for row in match_rows if not row.matched]

        return StagingMatchResponse(
            session_id=session_id,
            total_selected=len(selected_rows),
            matched_rows=matched_rows,
            unmatched_rows=unmatched_rows,
        )
    except HTTPException:
        raise


@router.get(
    "/seeds/session/{session_id}/staging/match",
    response_model=StagingMatchResponse,
)
async def get_last_match_results(
    session_id: str,
    staging_service=Depends(get_staging_service),
):
    """Return the most recent match results for this session."""
    try:
        rows = staging_service.get_match_rows(session_id)
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
    except HTTPException:
        raise


@router.post(
    "/seeds/session/{session_id}/staging/match/confirm",
    response_model=AddSeedsToSessionResponse,
)
async def confirm_matches(
    session_id: str,
    payload: ConfirmMatchesRequest,
    staging_service=Depends(get_staging_service),
    seed_session_service=Depends(get_seed_session_service),
):
    """Confirm matched rows and persist them as seeds."""
    try:
        rows = staging_service.get_match_rows(session_id)
        if not rows:
            raise HTTPException(status_code=400, detail="Match results not found. Run matching first.")

        allowed_ids = set(payload.staging_ids) if payload.staging_ids else None
        seeds = [
            row.matched_seed
            for row in rows
            if row.matched and row.matched_seed and (allowed_ids is None or row.staging_id in allowed_ids)
        ]

        if not seeds:
            raise HTTPException(status_code=400, detail="No matched seeds to confirm.")

        response = seed_session_service.set_seeds_for_session(session_id, seeds)
        return response
    except HTTPException:
        raise


@router.post(
    "/seeds/session/{session_id}/staging/{staging_id}/rematch",
    response_model=StagingMatchRow,
)
async def rematch_single_row(
    session_id: str,
    staging_id: int,
    payload: MatchSelectedRequest,
    staging_service=Depends(get_staging_service),
    match_service=Depends(get_staging_match_service),
):
    """Match a single staged paper after metadata edits."""
    try:
        row = staging_service.get_row(session_id, staging_id)
        match_rows = await match_service.match_rows(
            session_id=session_id,
            rows=[row],
            api_provider=payload.api_provider,
        )
        if not match_rows:
            raise HTTPException(status_code=400, detail="Unable to match this paper")
        new_row = match_rows[0]
        existing = staging_service.get_match_rows(session_id)
        replaced = False
        for idx, existing_row in enumerate(existing):
            if existing_row.staging_id == staging_id:
                existing[idx] = new_row
                replaced = True
                break
        if not replaced:
            existing.append(new_row)
        staging_service.store_match_rows(session_id, existing)
        return new_row
    except HTTPException:
        raise


@router.delete(
    "/seeds/session/{session_id}/staging/{staging_id}",
    response_model=BulkRemoveResponse,
)
async def delete_staged_paper(
    session_id: str,
    staging_id: int,
    service=Depends(get_staging_service),
):
    """Remove a single staged paper."""
    removed = service.remove_rows(session_id, [staging_id])
    stats = service.list_rows(session_id, page=1, page_size=1)
    return BulkRemoveResponse(removed_count=removed, total_rows=stats.total_rows)


@router.post(
    "/seeds/session/{session_id}/staging/remove",
    response_model=BulkRemoveResponse,
)
async def bulk_remove_staged_papers(
    session_id: str,
    payload: BulkRemoveRequest,
    service=Depends(get_staging_service),
):
    """Remove multiple staged papers."""
    removed = service.remove_rows(session_id, payload.staging_ids)
    stats = service.list_rows(session_id, page=1, page_size=1)
    return BulkRemoveResponse(removed_count=removed, total_rows=stats.total_rows)


@router.delete(
    "/seeds/session/{session_id}/staging",
)
async def clear_staging(
    session_id: str,
    service=Depends(get_staging_service),
):
    """Remove every staged paper for the session."""
    service.clear_session(session_id)
    return {"message": f"Cleared staging for session {session_id}"}


@router.get("/seeds/session/{session_id}/staging/{staging_id}/file")
async def download_staged_file(
    session_id: str,
    staging_id: int,
    staging_service=Depends(get_staging_service),
    source_file_service=Depends(get_source_file_service),
):
    """Return the original uploaded file for a staged row."""
    row = staging_service.get_row(session_id, staging_id)
    if not row.source_file_id:
        raise HTTPException(status_code=404, detail="No file stored for this staged paper")
    try:
        file_path = source_file_service.get_file_path(row.source_file_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Stored file could not be found")
    filename = row.source_file_name or file_path.name
    mime_type, _ = mimetypes.guess_type(filename)
    headers = {
        "Content-Disposition": f'inline; filename="{filename}"'
    }
    return FileResponse(
        path=file_path,
        media_type=mime_type or "application/octet-stream",
        filename=filename,
        headers=headers,
    )
