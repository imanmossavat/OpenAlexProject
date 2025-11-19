from fastapi import APIRouter, Depends, Path, Body
from pathlib import Path as FSPath

from app.schemas.configuration import (
    BasicConfigRequest,
    AdvancedConfigRequest,
    ConfigurationResponse,
    FinalizeConfigurationResponse,
    FinalizeConfigurationRequest,
)
from app.api.dependencies import (
    get_configuration_service,
    get_seed_session_service,
    get_keyword_service,
    get_library_service,
)
from app.core.exceptions import InvalidInputException

router = APIRouter()


@router.post("/{session_id}/config/basic", response_model=ConfigurationResponse)
async def set_basic_config(
    session_id: str = Path(..., description="Seed session ID"),
    request: BasicConfigRequest = Body(...),
    service = Depends(get_configuration_service)
):
    """
    Set basic crawler configuration.
    
    **Required settings:**
    - max_iterations: Maximum number of crawler iterations (≥ 1)
    - papers_per_iteration: Number of papers to sample per iteration (≥ 1)
    
    **Example:**
```json
    {
      "max_iterations": 5,
      "papers_per_iteration": 10
    }
```
    """
    service.set_basic_config(session_id, request)
    return service.get_configuration(session_id)


@router.post("/{session_id}/config/advanced", response_model=ConfigurationResponse)
async def set_advanced_config(
    session_id: str = Path(..., description="Seed session ID"),
    request: AdvancedConfigRequest = Body(...),
    service = Depends(get_configuration_service)
):
    """
    Set advanced crawler configuration (optional).
    
    **Optional settings:**
    - topic_model: Topic modeling algorithm ("NMF" or "LDA") - default: "NMF"
    - num_topics: Number of topics (2-100) - default: 20
    - save_figures: Save topic modeling figures - default: true
    - include_author_nodes: Include author nodes in graph - default: false
    - enable_retraction_watch: Enable retraction watch - default: true
    - additional_ignored_venues: Additional venues to ignore (beyond defaults)
    - language: Language code for text processing - default: "en"
    
    **Default ignored venues:** ArXiv, medRxiv, WWW, and empty string
    
    **Example:**
```json
    {
      "topic_model": "NMF",
      "num_topics": 30,
      "save_figures": true,
      "include_author_nodes": false,
      "enable_retraction_watch": true,
      "additional_ignored_venues": ["bioRxiv", "SSRN"],
      "language": "en"
    }
```
    """
    service.set_advanced_config(session_id, request)
    return service.get_configuration(session_id)


@router.get("/{session_id}/config", response_model=ConfigurationResponse)
async def get_configuration(
    session_id: str = Path(..., description="Seed session ID"),
    service = Depends(get_configuration_service)
):
    """
    Get current configuration for the session.
    
    Shows basic and advanced configuration with defaults filled in.
    """
    return service.get_configuration(session_id)


@router.delete("/{session_id}/config")
async def clear_configuration(
    session_id: str = Path(..., description="Seed session ID"),
    service = Depends(get_configuration_service)
):
    """
    Clear all configuration for the session.
    
    Resets both basic and advanced configuration.
    """
    service.clear_configuration(session_id)
    return {"message": "Configuration cleared", "session_id": session_id}


@router.post("/{session_id}/config/finalize", response_model=FinalizeConfigurationResponse)
async def finalize_configuration(
    session_id: str = Path(..., description="Seed session ID"),
    request: FinalizeConfigurationRequest = Body(...),
    config_service = Depends(get_configuration_service),
    session_service = Depends(get_seed_session_service),
    keyword_service = Depends(get_keyword_service),
    library_service = Depends(get_library_service),
):
    """
    Finalize configuration and prepare to start the crawler.
    """
    # Get keywords (optional)
    keywords = keyword_service.get_keywords(session_id)

    # Get configuration (validates basic config is set)
    config_dict = config_service.get_final_config_dict(session_id)

    total_seeds = 0
    api_provider = "openalex"

    library_path = request.library_path
    if library_path:
        # Validate library path and load info
        p = FSPath(library_path)
        if not p.is_absolute():
            raise InvalidInputException("Library path must be absolute")
        from ArticleCrawler.library.library_manager import LibraryManager
        lm = LibraryManager()
        lib_config = lm.load_library_config(p)
        api_provider = getattr(lib_config, "api_provider", api_provider) or api_provider
        # Count papers
        papers_dir = lm.get_papers_directory(p)
        total_seeds = len(list(papers_dir.glob("*.md"))) if papers_dir.exists() else 0

        # Persist selection for this session for later use by start endpoint
        name = request.library_name or lib_config.name or p.name
        library_service.set_details(
            session_id=session_id,
            name=name,
            path=str(p),
            description=getattr(lib_config, "description", None)
        )
    else:
        # Use seeds from the session
        seed_session = session_service.get_session(session_id)
        if not seed_session.seeds:
            raise InvalidInputException("No seeds selected. Please add seeds before finalizing.")

        # Always use OpenAlex
        api_provider = "openalex"
        total_seeds = len(seed_session.seeds)

    # Create summary
    config_summary = {
        "experiment_name": request.experiment_name,
        "api_provider": api_provider,
        "seeds": total_seeds,
        "keywords": len(keywords),
        "basic": {
            "max_iterations": config_dict["max_iterations"],
            "papers_per_iteration": config_dict["papers_per_iteration"]
        },
        "advanced": {
            "topic_model": config_dict["topic_model"],
            "num_topics": config_dict["num_topics"],
            "save_figures": config_dict["save_figures"],
            "include_author_nodes": config_dict["include_author_nodes"],
            "enable_retraction_watch": config_dict["enable_retraction_watch"],
            "ignored_venues": config_dict["ignored_venues"],
            "language": config_dict["language"]
        }
    }
    if library_path:
        config_summary["library_path"] = library_path
        if request.library_name:
            config_summary["library_name"] = request.library_name

    return FinalizeConfigurationResponse(
        session_id=session_id,
        experiment_name=request.experiment_name,
        message=f"Configuration finalized. Ready to start crawler '{request.experiment_name}'.",
        total_seeds=total_seeds,
        total_keywords=len(keywords),
        max_iterations=config_dict["max_iterations"],
        papers_per_iteration=config_dict["papers_per_iteration"],
        config_summary=config_summary
    )