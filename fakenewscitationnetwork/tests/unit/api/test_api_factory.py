import pytest
from ArticleCrawler.api import create_api_provider, get_available_providers


@pytest.mark.unit
class TestAPIFactory:
    
    def test_create_openalex_provider(self, mock_logger):
        provider = create_api_provider('openalex', logger=mock_logger)
        assert provider is not None
        assert hasattr(provider, 'get_paper')
        assert hasattr(provider, 'get_papers')
    
    def test_create_semantic_scholar_provider(self, mock_logger):
        provider = create_api_provider('semantic_scholar', wait=150, retries=2, logger=mock_logger)
        assert provider is not None
        assert hasattr(provider, 'get_paper')
    
    def test_create_with_alias_s2(self, mock_logger):
        provider = create_api_provider('s2', logger=mock_logger)
        assert provider is not None
    
    def test_invalid_provider_raises_error(self, mock_logger):
        with pytest.raises(ValueError, match="Unknown provider type"):
            create_api_provider('invalid_provider', logger=mock_logger)
    
    def test_get_available_providers(self):
        providers = get_available_providers()
        assert isinstance(providers, dict)
        assert 'semantic_scholar' in providers
        assert 'openalex' in providers