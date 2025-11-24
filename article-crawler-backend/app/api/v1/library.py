from fastapi import APIRouter, Depends, Path, Body, Query
from typing import List, Optional
from pathlib import Path as FSPath

from app.api.dependencies import (
    get_library_service,
    get_seed_session_service,
    get_library_edit_service,
    get_seed_selection_service,
    get_topic_modeling_service,
)
from app.schemas.library import (
    LibraryDetailsRequest,
    LibraryDetailsResponse,
    LibraryPreviewResponse,
    CreateLibraryResponse,
    LibraryInfo,
    LibraryListResponse,
    LibrarySelectRequest,
    LibrarySelectionResponse,
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
    clusters, overview_path, topics_folder = topic_service.run(
        details,
        model_type=request.model_type,
        num_topics=request.num_topics,
    )

    topics = [
        TopicSummary(topic_id=c.cluster_id, label=c.label, paper_count=len(c.paper_ids))
        for c in clusters
    ]
    total_with_papers = sum(1 for c in clusters if len(c.paper_ids) > 0)
    return StartTopicModelingResponse(
        session_id=session_id,
        model_type=request.model_type,
        num_topics=request.num_topics,
        total_topics_with_papers=total_with_papers,
        topics=topics,
        overview_path=str(overview_path),
        topics_folder=str(topics_folder),
    )


@router.get("/discover", response_model=LibraryListResponse)
async def discover_libraries():
    """Discover libraries in default search locations (ArticleCrawler's LibraryDiscovery)."""
    from ArticleCrawler.cli.utils.library_discovery import LibraryDiscovery
    disc = LibraryDiscovery()
    found = disc.find_libraries()
    items = []
    for lib in found:
        items.append(
            LibraryInfo(
                name=str(lib.get("name", "")),
                path=str(lib.get("path")),
                description=lib.get("description"),
                paper_count=int(lib.get("paper_count", 0) or 0),
                api_provider=lib.get("api_provider"),
                created_at=str(lib.get("created_at")) if lib.get("created_at") is not None else None,
            )
        )
    return LibraryListResponse(libraries=items)


@router.post("/{session_id}/select", response_model=LibrarySelectionResponse)
async def select_existing_library(
    session_id: str = Path(..., description="Session ID"),
    request: LibrarySelectRequest = Body(...),
    library_service = Depends(get_library_service)
):
    """Attach an existing library to the session (for Load/Edit flows)."""
    p = FSPath(request.path)
    if not p.is_absolute():
        raise ValueError("Library path must be absolute")
    if not (p / "library_config.yaml").exists():
        raise ValueError(f"Not a valid library: {p}")

    from ArticleCrawler.library.library_manager import LibraryManager
    lm = LibraryManager()
    config = lm.load_library_config(p)

    papers_dir = lm.get_papers_directory(p)
    paper_count = len(list(papers_dir.glob("*.md"))) if papers_dir.exists() else 0

    name = request.name or config.name or p.name
    details = library_service.set_details(
        session_id=session_id,
        name=name,
        path=str(p),
        description=getattr(config, "description", None)
    )

    return LibrarySelectionResponse(
        session_id=session_id,
        name=details["name"],
        path=details["path"],
        description=details.get("description"),
        paper_count=paper_count,
    )


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
    session_service = Depends(get_seed_session_service)
):
    result = library_service.create(session_id, session_service)
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
    library_service = Depends(get_library_service),
    edit_service = Depends(get_library_edit_service),
    seed_service = Depends(get_seed_selection_service)
):
    details = library_service.get_details(session_id)
    paper_ids: List[str] = []
    provider: Optional[str] = request.api_provider

    if request.seeds:
        paper_ids = [s.paper_id for s in request.seeds]
    elif request.paper_ids:
        match_result = seed_service.match_paper_ids(
            paper_ids=request.paper_ids,
            api_provider=request.api_provider
        )
        paper_ids = [ms.paper_id for ms in match_result.matched_seeds]
    else:
        raise ValueError("Provide either 'seeds' or 'paper_ids' in the request body")

    paper_ids = list(dict.fromkeys(paper_ids))

    result = edit_service.add_seeds(details, paper_ids, api_provider=provider)
    return AddLibrarySeedsResponse(
        session_id=session_id,
        api_provider=result["api_provider"],
        requested=result["requested"],
        added_count=result["added_count"],
        skipped_existing=result.get("skipped_existing", []),
        failed=result.get("failed", []),
        added_ids=result.get("added_ids", []),
    )


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
    library_service = Depends(get_library_service),
    edit_service = Depends(get_library_edit_service),
    session_service = Depends(get_seed_session_service)
):
    """
    Add all current session seeds (collected via Zotero/PDF/IDs) into the selected library.
    """
    details = library_service.get_details(session_id)
    session = session_service.get_session(session_id)
    paper_ids = [s.paper_id for s in session.seeds]
    paper_ids = list(dict.fromkeys(paper_ids))
    result = edit_service.add_seeds(details, paper_ids, api_provider=request.api_provider)
    return ApplySessionSeedsResponse(
        session_id=session_id,
        api_provider=result["api_provider"],
        requested=result["requested"],
        added_count=result["added_count"],
        skipped_existing=result.get("skipped_existing", []),
        failed=result.get("failed", []),
        added_ids=result.get("added_ids", []),
    )