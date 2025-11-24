from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.core.container import Container


@inject
async def get_seed_selection_service(
    service=Depends(Provide[Container.seed_selection_service])
):
    """Get the shared seed selection service."""
    return service


@inject
async def get_seed_session_service(
    service=Depends(Provide[Container.seed_session_service])
):
    """Get the seed session service."""
    return service


@inject
async def get_staging_service(
    service=Depends(Provide[Container.staging_service])
):
    """Get the staging service."""
    return service


@inject
async def get_pdf_seed_service(
    service=Depends(Provide[Container.pdf_seed_service])
):
    """Get the PDF seed service."""
    return service


@inject
async def get_zotero_seed_service(
    service=Depends(Provide[Container.zotero_seed_service])
):
    """Get the Zotero seed service."""
    return service


@inject
async def get_keyword_service(
    service=Depends(Provide[Container.keyword_service])
):
    """Get the keyword service."""
    return service


@inject
async def get_configuration_service(
    service=Depends(Provide[Container.configuration_service])
):
    """Get the configuration service."""
    return service


@inject
async def get_integration_settings_service(
    service=Depends(Provide[Container.integration_settings_service])
):
    """Get the integration settings service."""
    return service


@inject
async def get_crawler_execution_service(
    service=Depends(Provide[Container.crawler_execution_service])
):
    """Get the crawler execution service."""
    return service


@inject
async def get_library_service(
    service=Depends(Provide[Container.library_service])
):
    """Get the library service."""
    return service


@inject
async def get_library_edit_service(
    service=Depends(Provide[Container.library_edit_service])
):
    """Get the library edit service."""
    return service


@inject
async def get_topic_modeling_service(
    service=Depends(Provide[Container.topic_modeling_service])
):
    """Get the topic modeling service."""
    return service


@inject
async def get_author_topic_evolution_service(
    service=Depends(Provide[Container.author_topic_evolution_service])
):
    """Get the author topic evolution service."""
    return service
