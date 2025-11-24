from fastapi import APIRouter, Depends

from app.api.dependencies import get_integration_settings_service
from app.schemas.settings import (
    IntegrationSettingsResponse,
    UpdateOpenAlexSettingsRequest,
    UpdateZoteroSettingsRequest,
)

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/integrations", response_model=IntegrationSettingsResponse)
async def get_integration_settings(service=Depends(get_integration_settings_service)):
    """Return the stored integration credentials and status."""
    return service.get_settings()


@router.put("/openalex", response_model=IntegrationSettingsResponse)
async def update_openalex_settings(
    payload: UpdateOpenAlexSettingsRequest,
    service=Depends(get_integration_settings_service),
):
    """Update the OpenAlex polite email."""
    return service.update_openalex(payload)


@router.put("/zotero", response_model=IntegrationSettingsResponse)
async def update_zotero_settings(
    payload: UpdateZoteroSettingsRequest,
    service=Depends(get_integration_settings_service),
):
    """Update Zotero API credentials."""
    return service.update_zotero(payload)