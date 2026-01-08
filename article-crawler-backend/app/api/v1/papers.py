from fastapi import APIRouter, Depends

from app.api.dependencies import get_paper_metadata_service
from app.core.exceptions import to_http_exception
from app.schemas.papers import PaperDetail
from app.services.paper_metadata_service import PaperMetadataService

router = APIRouter()


@router.get("/{paper_id}", response_model=PaperDetail, summary="Fetch paper metadata")
async def get_paper_metadata(
    paper_id: str,
    service: PaperMetadataService = Depends(get_paper_metadata_service),
) -> PaperDetail:
    """
    Retrieve canonical metadata for a paper (title, authors, abstract, etc.).

    This proxies the request through the configured provider (OpenAlex) and normalizes
    the payload for the frontend modal.
    """
    try:
        return service.get_paper_details(paper_id)
    except Exception as exc:
        raise to_http_exception(exc)
