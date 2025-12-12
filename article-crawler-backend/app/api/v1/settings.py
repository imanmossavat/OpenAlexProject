from fastapi import APIRouter, Depends

from app.api.dependencies import get_integration_settings_service
from app.schemas.settings import (
    IntegrationSettingsResponse,
    LibraryRootSettings,
    UpdateLibraryRootRequest,
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


@router.get("/library-root", response_model=LibraryRootSettings)
async def get_library_root(service=Depends(get_integration_settings_service)):
    """Return the configured default library discovery root (if any)."""
    return service.get_library_root()


@router.put("/library-root", response_model=LibraryRootSettings)
async def update_library_root(
    payload: UpdateLibraryRootRequest,
    service=Depends(get_integration_settings_service),
):
    """Update or reset the default library discovery root."""
    return service.update_library_root(payload)
