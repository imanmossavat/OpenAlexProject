 
import pytest
from ArticleCrawler.config import SamplingConfig


@pytest.mark.unit
class TestSamplingConfig:
    
    def test_default_initialization(self):
        config = SamplingConfig(num_papers=10)
        assert config.num_papers == 10
        assert config.hyper_params == {'year': 0.1, 'centrality': 1.0}
        assert config.ignored_venues == []
        assert config.no_key_word_lambda == 1.0
    
    def test_custom_initialization(self):
        config = SamplingConfig(
            num_papers=5,
            hyper_params={'year': 0.2, 'centrality': 0.5},
            ignored_venues=['ArXiv', 'WWW'],
            no_key_word_lambda=0.5
        )
        assert config.num_papers == 5
        assert config.hyper_params['year'] == 0.2
        assert len(config.ignored_venues) == 2
        assert config.no_key_word_lambda == 0.5
    
    def test_invalid_num_papers_raises_error(self):
        with pytest.raises(ValueError, match="num_papers must be positive"):
            SamplingConfig(num_papers=0)
    
    def test_negative_lambda_raises_error(self):
        with pytest.raises(ValueError, match="no_key_word_lambda must be non-negative"):
            SamplingConfig(num_papers=1, no_key_word_lambda=-1)
    
    def test_copy_creates_independent_instance(self):
        config1 = SamplingConfig(num_papers=10, ignored_venues=['ArXiv'])
        config2 = config1.copy()
        config2.ignored_venues.append('WWW')
        assert len(config1.ignored_venues) == 1
        assert len(config2.ignored_venues) == 2