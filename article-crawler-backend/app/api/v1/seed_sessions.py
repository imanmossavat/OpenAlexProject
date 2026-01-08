from fastapi import APIRouter, Depends, Path

from app.schemas.seed_session import (
    StartSessionRequest,
    StartSessionResponse,
    SessionSeedsResponse,
    AddSeedsToSessionRequest,
    AddSeedsToSessionResponse,
    FinalizeSessionResponse
)
from app.schemas.seeds import PaperIDsRequest
from app.api.dependencies import (
    get_seed_session_service,
    get_seed_selection_service,
    get_source_file_service,
)

router = APIRouter()


@router.post("/start", response_model=StartSessionResponse)
async def start_seed_session(
    request: StartSessionRequest,
    service = Depends(get_seed_session_service)
):
    """
    Start a new seed selection session.
    
    Returns a session ID that should be used for all subsequent operations.
    """
    return service.start_session(request)


@router.get("/{session_id}", response_model=SessionSeedsResponse)
async def get_seed_session(
    session_id: str = Path(..., description="Session ID"),
    service = Depends(get_seed_session_service)
):
    """
    Get all seeds in a session.
    
    Returns the complete list of seeds added so far from all sources.
    """
    return service.get_session(session_id)


@router.post("/{session_id}/paper-ids", response_model=AddSeedsToSessionResponse)
async def add_paper_ids_to_session(
    session_id: str = Path(..., description="Session ID"),
    request: PaperIDsRequest = None,
    session_service = Depends(get_seed_session_service),
    seed_service = Depends(get_seed_selection_service)
):
    """
    Match paper IDs and add them to the session.
    
    This endpoint:
    1. Matches the paper IDs against the API
    2. Adds successfully matched seeds to the session
    3. Returns counts of added/duplicate seeds
    """
    match_result = seed_service.match_paper_ids(
        paper_ids=request.paper_ids,
        api_provider=request.api_provider
    )
    
    response = session_service.add_seeds_to_session(
        session_id=session_id,
        new_seeds=match_result.matched_seeds
    )
    
    return response


@router.post("/{session_id}/seeds", response_model=AddSeedsToSessionResponse)
async def add_seeds_to_session(
    session_id: str = Path(..., description="Session ID"),
    request: AddSeedsToSessionRequest = None,
    service = Depends(get_seed_session_service)
):
    """
    Add pre-matched seeds to the session.
    
    Use this when you already have MatchedSeed objects from another source.
    """
    return service.add_seeds_to_session(
        session_id=session_id,
        new_seeds=request.seeds
    )


@router.delete("/{session_id}/seeds/{paper_id}", response_model=SessionSeedsResponse)
async def remove_seed_from_session(
    session_id: str = Path(..., description="Session ID"),
    paper_id: str = Path(..., description="Paper ID to remove"),
    service = Depends(get_seed_session_service)
):
    """
    Remove a specific seed from the session.
    """
    return service.remove_seed_from_session(session_id, paper_id)


@router.post("/{session_id}/finalize", response_model=FinalizeSessionResponse)
async def finalize_seed_session(
    session_id: str = Path(..., description="Session ID"),
    service = Depends(get_seed_session_service)
):
    """
    Finalize the session and get all seeds.
    
    Use this when the user is done selecting seeds and wants to proceed
    to the next step (keywords, configuration, etc).
    """
    seeds = service.finalize_session(session_id)
    return FinalizeSessionResponse(
        session_id=session_id,
        total_seeds=len(seeds),
        seeds=seeds
    )


@router.delete("/{session_id}")
async def delete_seed_session(
    session_id: str = Path(..., description="Session ID"),
    service = Depends(get_seed_session_service),
    source_file_service = Depends(get_source_file_service),
):
    """
    Delete a session.
    """
    service.delete_session(session_id)
    source_file_service.cleanup_session_files(session_id)
    return {"message": f"Session {session_id} deleted successfully"}
