import pytest
from ArticleCrawler.config.temporal_config import TemporalAnalysisConfig


class TestTemporalAnalysisConfig:
    
    def test_default_initialization(self):
        config = TemporalAnalysisConfig()
        assert config.time_period_years == 3
        assert config.period_strategy == "fixed"
        assert config.min_papers_per_period == 2
        assert config.min_papers_total == 5
        assert config.include_partial_periods is True
        assert config.normalize_distributions is True
    
    def test_custom_initialization(self):
        config = TemporalAnalysisConfig(
            time_period_years=5,
            period_strategy="adaptive",
            min_papers_per_period=3,
            min_papers_total=10
        )
        assert config.time_period_years == 5
        assert config.period_strategy == "adaptive"
        assert config.min_papers_per_period == 3
        assert config.min_papers_total == 10
    
    def test_validate_success(self):
        config = TemporalAnalysisConfig()
        config.validate()
    
    def test_validate_invalid_time_period_years(self):
        config = TemporalAnalysisConfig(time_period_years=0)
        with pytest.raises(ValueError, match="time_period_years must be at least 1"):
            config.validate()
    
    def test_validate_invalid_min_papers_per_period(self):
        config = TemporalAnalysisConfig(min_papers_per_period=0)
        with pytest.raises(ValueError, match="min_papers_per_period must be at least 1"):
            config.validate()
    
    def test_validate_invalid_min_papers_total(self):
        config = TemporalAnalysisConfig(min_papers_total=0)
        with pytest.raises(ValueError, match="min_papers_total must be at least 1"):
            config.validate()
    
    def test_validate_invalid_emerging_threshold(self):
        config = TemporalAnalysisConfig(emerging_threshold=6.0)
        with pytest.raises(ValueError, match="emerging_threshold must be between 0 and 5"):
            config.validate()
    
    def test_validate_invalid_declining_threshold(self):
        config = TemporalAnalysisConfig(declining_threshold=-0.1)
        with pytest.raises(ValueError, match="declining_threshold must be between 0 and 5"):
            config.validate()
    
    def test_validate_custom_strategy_without_periods(self):
        config = TemporalAnalysisConfig(period_strategy="custom")
        with pytest.raises(ValueError, match="custom_periods must be provided"):
            config.validate()
    
    def test_validate_custom_strategy_with_periods(self):
        config = TemporalAnalysisConfig(
            period_strategy="custom",
            custom_periods=[(2020, 2022), (2023, 2025)]
        )
        config.validate()