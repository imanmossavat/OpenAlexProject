import pytest
from unittest.mock import Mock, patch
from ArticleCrawler.text_processing.text_analyzer import TextAnalysisManager


@pytest.mark.unit
class TestTextAnalysisManager:
    
    @pytest.fixture
    def text_analyzer(self, sample_text_config):
        return TextAnalysisManager(config=sample_text_config)
    
    def test_initialization(self, text_analyzer):
        assert text_analyzer.config is not None
        assert text_analyzer.preprocessing is not None
        assert text_analyzer.transformations is not None
        assert text_analyzer.topicmodeling is not None 
