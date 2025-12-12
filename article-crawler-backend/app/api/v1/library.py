from fastapi import APIRouter, Depends, Path, Body, Query
from typing import Optional
from pathlib import Path as FSPath

from app.api.dependencies import (
    get_library_service,
    get_seed_session_service,
    get_library_edit_service,
    get_topic_modeling_service,
    get_source_file_service,
    get_library_route_helper,
    get_library_edit_workflow_helper,
)
from app.schemas.library import (
    LibraryDetailsRequest,
    LibraryDetailsResponse,
    LibraryPreviewResponse,
    CreateLibraryResponse,
    LibraryListResponse,
    LibrarySelectRequest,
    LibrarySelectionResponse,
    LibraryEditSelectionResponse,
    LibraryEditCommitRequest,
    LibraryEditCommitResponse,
    AddLibrarySeedsRequest,
    AddLibrarySeedsResponse,
    RemoveLibrarySeedsRequest,
    RemoveLibrarySeedsResponse,
    LibraryContentsResponse,
    ApplySessionSeedsRequest,
    ApplySessionSeedsResponse,
)
from app.schemas.topic_modeling import (
    StartTopicModelingRequest,
    StartTopicModelingResponse,
    TopicSummary,
)


router = APIRouter()


@router.post("/{session_id}/details", response_model=LibraryDetailsResponse)
async def set_library_details(
    session_id: str = Path(..., description="Session ID"),
    request: LibraryDetailsRequest = Body(...),
    library_service = Depends(get_library_service)
):
    details = library_service.set_details(
        session_id=session_id,
        name=request.name,
        path=request.path,
        description=request.description
    )
    return LibraryDetailsResponse(
        session_id=session_id,
        name=details["name"],
        path=details["path"],
        description=details.get("description")
    )


@router.post("/{session_id}/topic-modeling/start", response_model=StartTopicModelingResponse)
async def start_topic_modeling(
    session_id: str = Path(..., description="Session ID"),
    request: StartTopicModelingRequest = Body(...),
    library_service = Depends(get_library_service),
    topic_service = Depends(get_topic_modeling_service)
):
    """
    Run topic modeling on the selected library and return labeled topics summary.
    """
    details = library_service.get_details(session_id)
    topic_result = topic_service.run(
        details,
        model_type=request.model_type,
        num_topics=request.num_topics,
    )
    clusters = topic_result["clusters"]

    topics = [
        TopicSummary(topic_id=c.cluster_id, label=c.label, paper_count=len(c.paper_ids))
        for c in clusters
    ]
    total_with_papers = sum(1 for c in clusters if len(c.paper_ids) > 0)
    overview_path = topic_result.get("overview_path")
    topics_folder = topic_result.get("topics_folder")
    return StartTopicModelingResponse(
        session_id=session_id,
        model_type=request.model_type,
        num_topics=request.num_topics,
        total_topics_with_papers=total_with_papers,
        topics=topics,
        overview_path=str(overview_path) if overview_path else "",
        topics_folder=str(topics_folder),
    )


@router.get("/discover", response_model=LibraryListResponse)
async def discover_libraries(
    query: Optional[str] = Query(None, description="Filter by name or description (case-insensitive)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(12, ge=1, le=100, alias="page_size", description="Items per page"),
    helper=Depends(get_library_route_helper),
):
    """Discover libraries in default search locations (ArticleCrawler's LibraryDiscovery)."""
    return helper.discover_libraries(query, page, page_size)


@router.post("/{session_id}/select", response_model=LibrarySelectionResponse)
async def select_existing_library(
    session_id: str = Path(..., description="Session ID"),
    request: LibrarySelectRequest = Body(...),
    helper=Depends(get_library_route_helper),
):
    """Attach an existing library to the session (for Load/Edit flows)."""
    return helper.select_existing_library(session_id, request)


@router.get("/{session_id}/preview", response_model=LibraryPreviewResponse)
async def preview_library(
    session_id: str = Path(..., description="Session ID"),
    library_service = Depends(get_library_service),
    session_service = Depends(get_seed_session_service)
):
    preview = library_service.preview(session_id, session_service)
    return LibraryPreviewResponse(
        session_id=session_id,
        name=preview["name"],
        path=preview["path"],
        description=preview.get("description"),
        total_papers=preview["total_papers"]
    )


@router.post("/{session_id}/create", response_model=CreateLibraryResponse)
async def create_library(
    session_id: str = Path(..., description="Session ID"),
    library_service = Depends(get_library_service),
    session_service = Depends(get_seed_session_service),
    source_file_service = Depends(get_source_file_service),
):
    result = library_service.create(session_id, session_service)
    source_file_service.cleanup_session_files(session_id)
    return CreateLibraryResponse(
        session_id=session_id,
        name=result["name"],
        base_path=result["base_path"],
        total_requested=result["total_requested"],
        saved_count=result["saved_count"],
        message=f"Library created at {result['base_path']}",
        papers=result.get("papers", [])
    )


@router.get("/{session_id}/contents", response_model=LibraryContentsResponse)
async def get_library_contents(
    session_id: str = Path(..., description="Session ID"),
    library_service = Depends(get_library_service),
    edit_service = Depends(get_library_edit_service)
):
    details = library_service.get_details(session_id)
    papers = edit_service.list_papers(details)
    from app.schemas.library import LibraryPaper
    paper_models = [LibraryPaper(**p) for p in papers]
    return LibraryContentsResponse(
        session_id=session_id,
        name=details.get("name") or FSPath(details.get("path")).name,
        path=details.get("path"),
        papers=paper_models,
        total_papers=len(paper_models)
    )


@router.post("/{session_id}/edit/add", response_model=AddLibrarySeedsResponse)
async def add_library_seeds(
    session_id: str = Path(..., description="Session ID"),
    request: AddLibrarySeedsRequest = Body(...),
    helper=Depends(get_library_route_helper),
):
    return helper.add_library_seeds(session_id, request)


@router.post("/{session_id}/edit/stage", response_model=LibraryEditSelectionResponse)
async def stage_library_for_editing(
    session_id: str = Path(..., description="Session ID"),
    helper=Depends(get_library_edit_workflow_helper),
):
    """Load an existing library into the staging/session workflow."""
    return helper.stage_library(session_id)


@router.post("/{session_id}/edit/remove", response_model=RemoveLibrarySeedsResponse)
async def remove_library_seeds(
    session_id: str = Path(..., description="Session ID"),
    request: RemoveLibrarySeedsRequest = Body(...),
    library_service = Depends(get_library_service),
    edit_service = Depends(get_library_edit_service)
):
    details = library_service.get_details(session_id)
    result = edit_service.remove_seeds(details, request.paper_ids)
    return RemoveLibrarySeedsResponse(
        session_id=session_id,
        requested=result["requested"],
        removed_count=result["removed_count"],
        not_found=result.get("not_found", []),
        removed_ids=result.get("removed_ids", []),
    )


@router.delete("/{session_id}/edit/seeds/{paper_id}", response_model=RemoveLibrarySeedsResponse)
async def remove_single_library_seed(
    session_id: str = Path(..., description="Session ID"),
    paper_id: str = Path(..., description="Paper ID to remove"),
    library_service = Depends(get_library_service),
    edit_service = Depends(get_library_edit_service)
):
    details = library_service.get_details(session_id)
    result = edit_service.remove_seeds(details, [paper_id])
    return RemoveLibrarySeedsResponse(
        session_id=session_id,
        requested=result["requested"],
        removed_count=result["removed_count"],
        not_found=result.get("not_found", []),
        removed_ids=result.get("removed_ids", []),
    )


@router.post("/{session_id}/edit/apply-session", response_model=ApplySessionSeedsResponse)
async def add_library_seeds_from_session(
    session_id: str = Path(..., description="Session ID"),
    request: ApplySessionSeedsRequest = Body(default=ApplySessionSeedsRequest()),
    helper=Depends(get_library_route_helper),
):
    """
    Add all current session seeds (collected via Zotero/PDF/IDs) into the selected library.
    """
    return helper.add_session_seeds(session_id, request)


@router.post("/{session_id}/edit/commit", response_model=LibraryEditCommitResponse)
async def commit_library_edits(
    session_id: str = Path(..., description="Session ID"),
    request: LibraryEditCommitRequest = Body(default=LibraryEditCommitRequest()),
    helper=Depends(get_library_edit_workflow_helper),
):
    """
    Apply the current session selections to the selected library or duplicate it elsewhere.
    """
    return helper.commit(session_id, request)
