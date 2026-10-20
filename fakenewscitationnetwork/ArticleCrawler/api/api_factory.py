import warnings
from typing import Dict, Any
from .base_api import BaseAPIProvider
from .semantic_scholar_api import SemanticScholarAPIProvider
from .openalex_api import OpenAlexAPIProvider

def create_api_provider(provider_type: str, **kwargs) -> BaseAPIProvider:
    """
    Factory to create API providers.
    
    Args:
        provider_type (str): Type of provider ('semantic_scholar' or 'openalex')
        **kwargs: Additional arguments to pass to the provider constructor
        
    Returns:
        BaseAPIProvider: Instance of the requested API provider
        
    Raises:
        ValueError: If provider_type is not recognized
    """
    provider_type = provider_type.lower()
    
    if provider_type in ['semantic_scholar', 's2', 'semanticscholar']:
        warnings.warn(
            "The Semantic Scholar provider is deprecated and unmaintained; use 'openalex'. "
            "See docs/decisions/semantic-scholar-to-openalex.md.",
            DeprecationWarning,
            stacklevel=2,
        )
        return SemanticScholarAPIProvider(**kwargs)
    elif provider_type in ['openalex', 'open_alex']:
        return OpenAlexAPIProvider(**kwargs)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}. "
                        f"Supported types: 'semantic_scholar', 'openalex'")

def get_available_providers() -> Dict[str, str]:
    """
    Get a dictionary of available providers and their descriptions.
    
    Returns:
        Dict[str, str]: Mapping of provider names to descriptions
    """
    return {
        'semantic_scholar': 'DEPRECATED - Semantic Scholar API using PyS2 library (not installed by default)',
        'openalex': 'OpenAlex API with full citation/reference enrichment'
    }