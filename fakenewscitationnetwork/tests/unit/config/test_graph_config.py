import pytest
from ArticleCrawler.config import GraphConfig


@pytest.mark.unit
class TestGraphConfig:
    
    def test_default_initialization(self):
        config = GraphConfig()
        assert config.ignored_venues == []
        assert config.include_author_nodes == False
        assert config.include_venue_nodes == True
        assert config.max_centrality_iterations == 1000
    
    def test_custom_initialization(self):
        config = GraphConfig(
            ignored_venues=['ArXiv', 'WWW'],
            include_author_nodes=True,
            max_centrality_iterations=500
        )
        assert len(config.ignored_venues) == 2
        assert config.include_author_nodes == True
        assert config.max_centrality_iterations == 500
    
    def test_invalid_max_iterations_raises_error(self):
        with pytest.raises(ValueError, match="max_centrality_iterations must be positive"):
            GraphConfig(max_centrality_iterations=0)
    
    def test_copy_creates_independent_instance(self):
        config1 = GraphConfig(ignored_venues=['ArXiv'])
        config2 = config1.copy()
        config2.ignored_venues.append('WWW')
        assert len(config1.ignored_venues) == 1
        assert len(config2.ignored_venues) == 2 
