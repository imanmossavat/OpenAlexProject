from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import FileResponse
import mimetypes

from app.api.dependencies import (
    get_retraction_service,
    get_source_file_service,
    get_staging_service,
    get_staging_route_helper,
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
    helper=Depends(get_staging_route_helper),
):
    """Return paginated staged papers for a session."""
    return helper.list_staged_papers(
        session_id,
        page=page,
        page_size=page_size,
        sources=sources,
        year_min=year_min,
        year_max=year_max,
        title=title,
        venue=venue,
        author=author,
        keyword=keyword,
        doi_presence=doi_presence,
        retraction_status=retraction_status,
        title_values=title_values,
        author_values=author_values,
        venue_values=venue_values,
        year_values=year_values,
        identifier_values=identifier_values,
        column_filters=column_filters,
        selected_only=selected_only,
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
    helper=Depends(get_staging_route_helper),
):
    """Add papers to the staging table."""
    return await helper.add_staged_papers(session_id, payload)


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
    helper=Depends(get_staging_route_helper),
):
    """Toggle selection for multiple staged papers."""
    return helper.update_selection(session_id, payload)


@router.post(
    "/seeds/session/{session_id}/staging/match",
    response_model=StagingMatchResponse,
)
async def match_selected_rows(
    session_id: str,
    payload: MatchSelectedRequest,
    helper=Depends(get_staging_route_helper),
):
    """Match currently selected staged rows using DOI/title heuristics."""
    return await helper.match_selected_rows(session_id, payload)


@router.get(
    "/seeds/session/{session_id}/staging/match",
    response_model=StagingMatchResponse,
)
async def get_last_match_results(
    session_id: str,
    helper=Depends(get_staging_route_helper),
):
    """Return the most recent match results for this session."""
    return helper.get_last_match_results(session_id)


@router.post(
    "/seeds/session/{session_id}/staging/match/confirm",
    response_model=AddSeedsToSessionResponse,
)
async def confirm_matches(
    session_id: str,
    payload: ConfirmMatchesRequest,
    helper=Depends(get_staging_route_helper),
):
    """Confirm matched rows and persist them as seeds."""
    return helper.confirm_matches(session_id, payload.staging_ids)


@router.post(
    "/seeds/session/{session_id}/staging/{staging_id}/rematch",
    response_model=StagingMatchRow,
)
async def rematch_single_row(
    session_id: str,
    staging_id: int,
    payload: MatchSelectedRequest,
    helper=Depends(get_staging_route_helper),
):
    """Match a single staged paper after metadata edits."""
    return await helper.rematch_single_row(session_id, staging_id, payload)


@router.delete(
    "/seeds/session/{session_id}/staging/{staging_id}",
    response_model=BulkRemoveResponse,
)
async def delete_staged_paper(
    session_id: str,
    staging_id: int,
    helper=Depends(get_staging_route_helper),
):
    """Remove a single staged paper."""
    return helper.remove_single_paper(session_id, staging_id)


@router.post(
    "/seeds/session/{session_id}/staging/remove",
    response_model=BulkRemoveResponse,
)
async def bulk_remove_staged_papers(
    session_id: str,
    payload: BulkRemoveRequest,
    helper=Depends(get_staging_route_helper),
):
    """Remove multiple staged papers."""
    return helper.remove_staged_papers(session_id, payload)


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
