
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from typing import List

from app.services.zotero_seed_service import ZoteroSeedService
from app.services.seed_session_service import SeedSessionService
from app.api.dependencies import get_zotero_seed_service, get_seed_session_service, get_staging_service

from app.schemas.zotero_seeds import (
    ZoteroCollectionsResponse,
    ZoteroCollectionItemsResponse,
    ZoteroItemMetadata,
    StageItemsRequest,
    StageItemsResponse,
    StagedItemsResponse,
    ZoteroMatchRequest,
    ZoteroMatchResponse,
    ZoteroConfirmRequest,
    ZoteroConfirmResponse,
    ManualMatchSelection,
)
from app.schemas.staging import StagingPaperCreate


router = APIRouter(prefix="/seeds/session/{session_id}/zotero", tags=["zotero_seeds"])


@router.get("/availability")
async def check_zotero_availability(
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service)
):
    """
    Check if Zotero is properly configured.
    
    Returns status and helpful error message if not available.
    """
    is_available, error_msg = zotero_service.check_zotero_availability()
    
    if is_available:
        return {
            "available": True,
            "message": "Zotero is properly configured"
        }
    else:
        return {
            "available": False,
            "message": error_msg or "Zotero not configured",
            "help": (
                "Add to your .env file:\n"
                "ZOTERO_LIBRARY_ID=your_library_id\n"
                "ZOTERO_API_KEY=your_api_key\n"
                "Get credentials from: https://www.zotero.org/settings/keys"
            )
        }


@router.get("/collections", response_model=ZoteroCollectionsResponse)
async def get_zotero_collections(
    session_id: str = Path(..., description="Session ID"),
    session_service: SeedSessionService = Depends(get_seed_session_service),
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service)
):
    """
    Get all Zotero collections for the user.
    
    """
    session_service.get_session(session_id)
    
    collections = zotero_service.get_collections(session_id)
    
    return ZoteroCollectionsResponse(
        collections=collections,
        total_count=len(collections)
    )
    


@router.get("/collections/{collection_key}/items", response_model=ZoteroCollectionItemsResponse)
async def get_collection_items(
    session_id: str = Path(..., description="Session ID"),
    collection_key: str = Path(..., description="Zotero collection key"),
    session_service: SeedSessionService = Depends(get_seed_session_service),
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service)
):
    """
    Get all items from a specific Zotero collection.
    
    Returns items that can be staged individually or all at once.
    This allows users to browse a collection before deciding what to stage.
    """
    session_service.get_session(session_id)
    
    collection_name, items = zotero_service.get_collection_items(
        session_id, 
        collection_key
    )
    
    return ZoteroCollectionItemsResponse(
        collection_key=collection_key,
        collection_name=collection_name,
        items=items,
        total_count=len(items)
    )
    


@router.post("/collections/{collection_key}/stage", response_model=StageItemsResponse)
async def stage_items_from_collection(
    session_id: str = Path(..., description="Session ID"),
    collection_key: str = Path(..., description="Zotero collection key"),
    request: StageItemsRequest = Body(...),
    session_service: SeedSessionService = Depends(get_seed_session_service),
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service),
    staging_service=Depends(get_staging_service),
):
    """
    Stage items from a collection.
    
    Can be called multiple times for different collections.
    
    Actions:
    - "stage_all": Stage all items from the collection
    - "stage_selected": Stage only the items specified in selected_items
    """
    session_service.get_session(session_id)
    
    collection_name, all_items = zotero_service.get_collection_items(
        session_id,
        collection_key
    )
    
    if request.action == "stage_all":
        items_to_stage = all_items
    else:
        if not request.selected_items:
            raise HTTPException(
                status_code=400,
                detail="selected_items is required when action is 'stage_selected'"
            )
        
        selected_keys = set(request.selected_items)
        items_to_stage = [
            item for item in all_items 
            if item.zotero_key in selected_keys
        ]
        
        if len(items_to_stage) != len(request.selected_items):
            raise HTTPException(
                status_code=400,
                detail="Some selected items not found in collection"
            )
    
    staged_count = zotero_service.stage_items(session_id, items_to_stage)
    
    author_str = lambda authors: ', '.join(authors[:3]) + (' et al.' if len(authors) > 3 else '') if authors else None
    staging_rows = [
        StagingPaperCreate(
            source=f"Zotero - {collection_name}" if collection_name else "Zotero",
            source_type="zotero",
            title=item.title,
            authors=author_str(item.authors),
            year=item.year,
            venue=item.publication or None,
            doi=item.doi,
            url=item.url,
            abstract=item.abstract,
            source_id=item.zotero_key,
            is_selected=False,
        )
        for item in items_to_stage
    ]
    added_rows = staging_service.add_rows(session_id, staging_rows) if staging_rows else []
    
    stats = staging_service.list_rows(session_id, page=1, page_size=1)
    
    action_text = "all items" if request.action == "stage_all" else f"{len(items_to_stage)} selected items"
    
    return StageItemsResponse(
        staged_count=len(added_rows),
        total_staged=stats.total_rows,
        message=f"Added {len(added_rows)} papers from {action_text} to the staging table"
    )
    


@router.get("/staged-items", response_model=StagedItemsResponse)
async def get_staged_items(
    session_id: str = Path(..., description="Session ID"),
    session_service: SeedSessionService = Depends(get_seed_session_service),
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service)
):
    """
    Get all staged items from multiple collections.
    
    This is step 3 of the Zotero workflow.
    Shows items staged from all collections before matching.
    """
    session_service.get_session(session_id)
    
    staged_items_raw = zotero_service.get_staged_items(session_id)
    staged_items = [
        ZoteroItemMetadata.model_validate(item)
        for item in staged_items_raw
    ]
    
    collection_keys = {item.collection_key for item in staged_items}
    collections_cache = zotero_service._collections_cache.get(session_id, {})
    collection_names = [
        collections_cache.get(key, f"Collection {key}")
        for key in collection_keys
    ]
    
    return StagedItemsResponse(
        staged_items=staged_items,
        total_count=len(staged_items),
        collections=collection_names
    )
    


@router.delete("/staged-items/{zotero_key}")
async def remove_staged_item(
    session_id: str = Path(..., description="Session ID"),
    zotero_key: str = Path(..., description="Zotero item key to remove"),
    session_service: SeedSessionService = Depends(get_seed_session_service),
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service)
):
    """
    Remove a specific item from the staging area.
    
    Allows users to remove items they don't want before matching.
    """
    session_service.get_session(session_id)
    
    zotero_service.remove_staged_item(session_id, zotero_key)
    
    remaining = zotero_service.get_staged_items(session_id)
    
    return {
        "message": f"Successfully removed item {zotero_key} from staging",
        "remaining_count": len(remaining)
    }
    


@router.post("/match", response_model=ZoteroMatchResponse)
async def match_staged_items(
    session_id: str = Path(..., description="Session ID"),
    request: ZoteroMatchRequest = Body(...),
    session_service: SeedSessionService = Depends(get_seed_session_service),
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service)
):
    """
    Match all staged items against API provider.
    
    This is step 4 of the Zotero workflow.
    Matches items by DOI first, then falls back to title search.
    
    **Returns:**
    - **Auto-matched papers** (confidence ≥ 85%): `matched=True`, `paper_id` is set
    - **Papers needing review** (60% ≤ confidence < 85%): `matched=False`, `candidates` list provided
    - **Failed matches**: `matched=False`, no candidates
    
    For papers with candidates, use the `/review` endpoint to manually select.
    """
    session_service.get_session(session_id)
    
    results = zotero_service.match_staged_items(
        session_id,
        api_provider=request.api_provider
    )
    
    matched_count = sum(1 for r in results if r.matched)
    unmatched_count = len(results) - matched_count
    
    return ZoteroMatchResponse(
        results=results,
        total_items=len(results),
        matched_count=matched_count,
        unmatched_count=unmatched_count
    )
    


@router.post("/review")
async def review_manual_matches(
    session_id: str = Path(..., description="Session ID"),
    manual_selections: List[ManualMatchSelection] = Body(..., description="Manual selections for papers with candidates"),
    session_service: SeedSessionService = Depends(get_seed_session_service),
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service)
):
    """
    Submit manual selections for papers that need review.
    
    This is step 4b (optional) - only needed if match results contain papers with candidates.
    
    **For each paper with candidates, specify:**
    - `{"zotero_key": "...", "action": "select", "selected_paper_id": "W123"}` - Select a candidate
    - `{"zotero_key": "...", "action": "skip"}` - Skip this paper
    
    These selections will be used in the final confirmation step.
    You can also skip this endpoint and just provide manual_selections directly in the `/confirm` endpoint.
    """
    session_service.get_session(session_id)
    

    selections = [sel.model_dump() for sel in manual_selections]
    
    if not hasattr(zotero_service, '_manual_selections_storage'):
        zotero_service._manual_selections_storage = {}
    
    zotero_service._manual_selections_storage[session_id] = selections
    
    selected_count = sum(1 for s in selections if s.get('action') == 'select')
    skipped_count = sum(1 for s in selections if s.get('action') == 'skip')
    
    return {
        "message": "Manual selections recorded",
        "selected_count": selected_count,
        "skipped_count": skipped_count,
        "total_reviewed": len(selections)
    }
    


@router.post("/confirm", response_model=ZoteroConfirmResponse)
async def confirm_matches(
    session_id: str = Path(..., description="Session ID"),
    request: ZoteroConfirmRequest = Body(...),
    session_service: SeedSessionService = Depends(get_seed_session_service),
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service),
    staging_service = Depends(get_staging_service),
):
    """
    Confirm matches and add seeds to session.
    
    This is step 5 (final step) of the Zotero workflow.
    
    **Workflow:**
    1. Auto-matched papers (confidence ≥ 85%) are automatically included if action is 'accept_all'
    2. Papers that needed manual review are included based on manual_selections (either from /review or provided here)
    3. Failed matches are excluded
    
    **Actions:**
    - **accept_all**: Add all auto-matched + manually selected papers to session
    - **skip_all**: Don't add any papers to session
    
    **Manual Selections (optional if already submitted via /review):**
    For papers that couldn't be auto-matched but have candidates, provide:
    - `{"zotero_key": "...", "action": "select", "selected_paper_id": "W123"}` to select a candidate
    - `{"zotero_key": "...", "action": "skip"}` to skip that paper
    
    Staging area is cleared after confirmation.
    """
    session = session_service.get_session(session_id)
    
    manual_selections = [sel.model_dump() for sel in (request.manual_selections or [])]
    
    if not manual_selections and hasattr(zotero_service, '_manual_selections_storage'):
        manual_selections = zotero_service._manual_selections_storage.get(session_id, [])
    
    seeds = zotero_service.get_confirmed_seeds(
        session_id,
        request.action,
        manual_selections
    )

    staging_rows = [
        StagingPaperCreate(
            source=seed.source or "Zotero",
            source_type=seed.source_type or "zotero",
            title=seed.title,
            authors=seed.authors,
            year=seed.year,
            venue=seed.venue,
            doi=seed.doi,
            url=seed.url,
            abstract=seed.abstract,
            source_id=seed.source_id or seed.paper_id,
            is_selected=False,
        )
        for seed in seeds
    ]
    staged = staging_service.add_rows(session_id, staging_rows) if staging_rows else []
    
    zotero_service.clear_staging(session_id)
    if hasattr(zotero_service, '_manual_selections_storage') and session_id in zotero_service._manual_selections_storage:
        del zotero_service._manual_selections_storage[session_id]
    
    stats = staging_service.list_rows(session_id, page=1, page_size=1)
    
    accepted_count = len(staged)
    match_results = zotero_service._match_results_storage.get(session_id, [])
    total_matched = len([r for r in match_results if r.matched])
    total_manual = len(manual_selections)
    skipped_count = 0 if request.action == "accept_all" else (total_matched + total_manual)
    
    return ZoteroConfirmResponse(
        accepted_count=accepted_count,
        skipped_count=skipped_count,
        total_seeds_in_session=stats.total_rows,
        message=f"Successfully added {accepted_count} papers to staging"
    )
    


@router.delete("/clear-staging")
async def clear_staging(
    session_id: str = Path(..., description="Session ID"),
    session_service: SeedSessionService = Depends(get_seed_session_service),
    zotero_service: ZoteroSeedService = Depends(get_zotero_seed_service)
):
    """
    Clear the staging area without adding seeds to session.
    
    Useful if user wants to start over with Zotero selection.
    """
    session_service.get_session(session_id)
    
    zotero_service.clear_staging(session_id)
    
    return {
        "message": "Successfully cleared staging area"
    }
