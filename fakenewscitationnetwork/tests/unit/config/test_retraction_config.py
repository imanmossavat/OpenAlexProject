import pytest
from ArticleCrawler.config import RetractionConfig


@pytest.mark.unit
class TestRetractionConfig:
    
    def test_default_initialization(self):
        config = RetractionConfig()
        assert config.enable_retraction_watch == True
        assert config.avoid_retraction_in_sampler == False
        assert config.avoid_retraction_in_reporting == True
        assert 'gitlab.com' in config.retraction_watch_raw_url
    
    def test_custom_initialization(self):
        config = RetractionConfig(
            enable_retraction_watch=False,
            avoid_retraction_in_sampler=True,
            avoid_retraction_in_reporting=False
        )
        assert config.enable_retraction_watch == False
        assert config.avoid_retraction_in_sampler == True
        assert config.avoid_retraction_in_reporting == False
    
    def test_copy_creates_independent_instance(self):
        config1 = RetractionConfig(enable_retraction_watch=True)
        config2 = config1.copy()
        config2.enable_retraction_watch = False
        assert config1.enable_retraction_watch == True
        assert config2.enable_retraction_watch == False 
