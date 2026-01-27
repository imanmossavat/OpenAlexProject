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
async def get_staging_query_parser(
    service=Depends(Provide[Container.staging_query_parser])
):
    """Get the staging query parser."""
    return service


@inject
async def get_manual_metadata_enricher(
    service=Depends(Provide[Container.manual_metadata_enricher])
):
    """Get the manual metadata enricher."""
    return service


@inject
async def get_staging_match_service(
    service=Depends(Provide[Container.staging_match_service])
):
    """Get the staging match service."""
    return service


@inject
async def get_retraction_service(
    service=Depends(Provide[Container.retraction_service])
):
    """Get the retraction watch service."""
    return service


@inject
async def get_pdf_seed_service(
    service=Depends(Provide[Container.pdf_seed_service])
):
    """Get the PDF seed service."""
    return service


@inject
async def get_pdf_seed_workflow_service(
    service=Depends(Provide[Container.pdf_seed_workflow_service])
):
    """Get the PDF seed workflow service."""
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


@inject
async def get_source_file_service(
    service=Depends(Provide[Container.source_file_service])
):
    """Get the persisted source file service."""
    return service


@inject
async def get_paper_metadata_service(
    service=Depends(Provide[Container.paper_metadata_service])
):
    """Get the paper metadata service."""
    return service


@inject
async def get_paper_catalog_service(
    service=Depends(Provide[Container.paper_catalog_service])
):
    """Get the paper catalog service."""
    return service


@inject
async def get_zotero_export_service(
    service=Depends(Provide[Container.zotero_export_service])
):
    """Get the Zotero export coordinator."""
    return service


@inject
async def get_library_route_helper(
    helper=Depends(Provide[Container.library_route_helper])
):
    """Get the helper that encapsulates library route logic."""
    return helper


@inject
async def get_library_edit_workflow_helper(
    helper=Depends(Provide[Container.library_edit_workflow_helper])
):
    """Get the helper that orchestrates the edit workflow."""
    return helper


@inject
async def get_staging_route_helper(
    helper=Depends(Provide[Container.staging_route_helper])
):
    """Get the helper that encapsulates staging route logic."""
    return helper


@inject
async def get_seed_route_helper(
    helper=Depends(Provide[Container.seed_route_helper])
):
    """Get the helper that encapsulates seed route logic."""
    return helper


@inject
async def get_crawler_rerun_service(
    service=Depends(Provide[Container.crawler_rerun_service])
):
    """Get the crawler rerun service."""
    return service
