from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.dependencies import (
    get_crawler_execution_service,
    get_zotero_export_service,
)
from app.schemas.zotero_export import ZoteroExportRequest, ZoteroExportResponse
from app.schemas.zotero_seeds import ZoteroCollection, ZoteroCollectionsResponse

router = APIRouter(prefix="/zotero", tags=["Zotero"])


@router.get("/collections", response_model=ZoteroCollectionsResponse)
async def list_zotero_collections(
    export_service=Depends(get_zotero_export_service),
):
    """Return all accessible Zotero collections for the configured credentials."""
    collections_raw = export_service.list_collections()
    collections = []
    for col in collections_raw:
        parent_collection = (col.get("data") or {}).get("parentCollection")
        if not isinstance(parent_collection, str) or not parent_collection:
            parent_collection = None

        collections.append(
            ZoteroCollection(
                key=col["key"],
                name=col["name"],
                parent_collection=parent_collection,
            )
        )
    return ZoteroCollectionsResponse(collections=collections, total_count=len(collections))


@router.post(
    "/crawler/jobs/{job_id}/export",
    response_model=ZoteroExportResponse,
    summary="Export selected job papers to Zotero",
)
async def export_job_papers_to_zotero(
    job_id: str = Path(..., description="Crawler job identifier"),
    payload: ZoteroExportRequest = ...,
    crawler_service=Depends(get_crawler_execution_service),
    export_service=Depends(get_zotero_export_service),
):
    """Export selected catalog papers to Zotero."""
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}. Export is available only for completed jobs.",
        )

    return export_service.export(job_id, payload)
