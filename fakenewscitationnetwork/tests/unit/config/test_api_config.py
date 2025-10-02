import pytest
from ArticleCrawler.config import APIConfig, OpenAlexConfig, SemanticScholarConfig


@pytest.mark.unit
class TestAPIConfig:
    
    def test_default_initialization(self):
        config = APIConfig()
        assert config.provider_type == 'openalex'
        assert config.retries == 3
        assert config.wait is None
    
    def test_custom_initialization(self):
        config = APIConfig(provider_type='semantic_scholar', wait=200, retries=5)
        assert config.provider_type == 'semantic_scholar'
        assert config.wait == 200
        assert config.retries == 5
    
    def test_invalid_provider_type_raises_error(self):
        with pytest.raises(ValueError, match="Invalid provider_type"):
            APIConfig(provider_type='invalid_api')
    
    def test_provider_type_normalization(self):
        config = APIConfig(provider_type='OpenAlex')
        assert config.provider_type == 'openalex'
    
    def test_get_provider_kwargs(self):
        config = APIConfig(provider_type='openalex', wait=100, retries=2, custom_param='value')
        kwargs = config.get_provider_kwargs()
        assert kwargs['wait'] == 100
        assert kwargs['retries'] == 2
        assert kwargs['custom_param'] == 'value'
    
    def test_copy_creates_independent_instance(self):
        config1 = APIConfig(provider_type='openalex', retries=3)
        config2 = config1.copy()
        config2.retries = 5
        assert config1.retries == 3
        assert config2.retries == 5


@pytest.mark.unit
class TestOpenAlexConfig:
    
    def test_default_initialization(self):
        config = OpenAlexConfig()
        assert config.provider_type == 'openalex'
        assert config.retries == 3
        assert config.wait is None
    
    def test_custom_parameters(self):
        config = OpenAlexConfig(retries=5, requests_per_second=10, email='test@example.com')
        kwargs = config.get_provider_kwargs()
        assert kwargs['retries'] == 5
        assert kwargs['email'] == 'test@example.com'


@pytest.mark.unit
class TestSemanticScholarConfig:
    
    def test_default_initialization(self):
        config = SemanticScholarConfig()
        assert config.provider_type == 'semantic_scholar'
        assert config.wait == 150
        assert config.retries == 2
    
    def test_custom_parameters(self):
        config = SemanticScholarConfig(wait=200, retries=5)
        assert config.wait == 200
        assert config.retries == 5