from fastapi import APIRouter, Depends
from app.schemas.seeds import PaperIDsRequest, PaperIDsResponse
from app.api.dependencies import get_seed_selection_service

router = APIRouter()


@router.post("/paper-ids", response_model=PaperIDsResponse)
async def match_paper_ids(
    request: PaperIDsRequest,
    service = Depends(get_seed_selection_service)
):
    """
    Match paper IDs against an API provider.
    
    This endpoint is independent of any specific use case and can be called
    by crawler wizard, library creation, or any other feature that needs seeds.
    
    **Supported paper ID formats:**
    - OpenAlex IDs: W123456789
    - DOIs: 10.1234/example or https://doi.org/10.1234/example
    - Semantic Scholar IDs: (when using semantic_scholar provider)
    
    **Returns:**
    - List of successfully matched seeds with metadata
    - List of seeds that could not be matched with error messages
    """
    result = service.match_paper_ids(
        paper_ids=request.paper_ids,
        api_provider=request.api_provider
    )
    return PaperIDsResponse(result=result)