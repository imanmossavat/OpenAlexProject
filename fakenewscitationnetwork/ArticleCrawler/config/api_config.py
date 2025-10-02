from typing import Dict, Any, Optional

class APIConfig:
    """
    Configuration for API providers and their specific settings.
    
    This class handles all API-related configuration including provider selection,
    authentication, rate limiting, and provider-specific parameters.
    """
    
    def __init__(self, 
                 provider_type: str = 'openalex',
                 wait: Optional[int] = None,
                 retries: int = 3,
                 **provider_kwargs):
        """
        Initialize API configuration.
        
        Args:
            provider_type (str): Type of API provider ('openalex' or 'semantic_scholar')
            wait (int, optional): Wait time between requests (provider-specific default used if None)
            retries (int): Number of retries for failed requests
            **provider_kwargs: Additional provider-specific arguments
        """
        self.provider_type = provider_type.lower()
        self.wait = wait
        self.retries = retries
        self.provider_kwargs = provider_kwargs
        
        valid_providers = ['openalex', 'semantic_scholar', 's2', 'open_alex']
        if self.provider_type not in valid_providers:
            raise ValueError(f"Invalid provider_type: {provider_type}. "
                           f"Valid options: {valid_providers}")
    
    def get_provider_kwargs(self) -> Dict[str, Any]:
        """
        Get all arguments to pass to the API provider constructor.
        
        Returns:
            Dict[str, Any]: Combined configuration for provider initialization
        """
        kwargs = self.provider_kwargs.copy()
        
        if self.wait is not None:
            kwargs['wait'] = self.wait
        kwargs['retries'] = self.retries
        
        return kwargs
    
    def copy(self):
        """Create a copy of this configuration."""
        return APIConfig(
            provider_type=self.provider_type,
            wait=self.wait,
            retries=self.retries,
            **self.provider_kwargs.copy()
        )

class SemanticScholarConfig(APIConfig):
    """Semantic Scholar specific configuration with sensible defaults."""
    
    def __init__(self, wait: int = 150, retries: int = 2, **kwargs):
        super().__init__(
            provider_type='semantic_scholar',
            wait=wait,
            retries=retries,
            **kwargs
        )

class OpenAlexConfig(APIConfig):
    """OpenAlex specific configuration with sensible defaults."""
    
    def __init__(self, 
                 retries: int = 3,
                 requests_per_second: int = 8,
                 email: Optional[str] = None,
                 **kwargs):
        if email:
            kwargs['email'] = email
        if requests_per_second != 8:
            kwargs['requests_per_second'] = requests_per_second
            
        super().__init__(
            provider_type='openalex',
            wait=None,
            retries=retries,
            **kwargs
        )