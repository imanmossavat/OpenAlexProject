import pytest
from ArticleCrawler.config import StoppingConfig


@pytest.mark.unit
class TestStoppingConfig:
    
    def test_default_initialization(self):
        config = StoppingConfig()
        assert config.max_iter == 1
        assert config.max_df_size == 1E9
    
    def test_custom_initialization(self):
        config = StoppingConfig(max_iter=10, max_df_size=5000)
        assert config.max_iter == 10
        assert config.max_df_size == 5000
    
    def test_invalid_max_iter_raises_error(self):
        with pytest.raises(ValueError, match="max_iter must be positive"):
            StoppingConfig(max_iter=0)
    
    def test_invalid_max_df_size_raises_error(self):
        with pytest.raises(ValueError, match="max_df_size must be positive"):
            StoppingConfig(max_df_size=-100)
    
    def test_copy_creates_independent_instance(self):
        config1 = StoppingConfig(max_iter=5)
        config2 = config1.copy()
        config2.max_iter = 10
        assert config1.max_iter == 5
        assert config2.max_iter == 10 
