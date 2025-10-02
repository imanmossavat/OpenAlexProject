import pytest
import pandas as pd
from unittest.mock import Mock
from ArticleCrawler.text_processing.preprocessing import TextPreProcessing


@pytest.mark.unit
class TestTextPreProcessing:
    
    @pytest.fixture
    def preprocessor(self, sample_text_config):
        return TextPreProcessing(config=sample_text_config)
    
    def test_remove_special_characters_from_string(self, preprocessor):
        text = "This is <jats:italic>formatted</jats:italic> text!"
        cleaned = preprocessor.remove_special_characters(text)
        assert "<jats:italic>" not in cleaned
    
    def test_remove_special_characters_from_series(self, preprocessor):
        series = pd.Series(["Text with <tag>", "Another <tag> text"])
        cleaned = preprocessor.remove_special_characters(series)
        assert isinstance(cleaned, pd.Series)
        assert "<tag>" not in cleaned.iloc[0]
    
    def test_get_invalid_indices_filters_none_values(self, preprocessor):
        abstracts = pd.Series([None, "Valid abstract with enough length for the minimum requirement", "Another one"], index=[0, 1, 2])
        invalid_indices = preprocessor.get_invalid_indices(abstracts, Mock())
        assert 0 in invalid_indices
    
    def test_get_invalid_indices_filters_short_abstracts(self, preprocessor):
        abstracts = pd.Series([
            "Short", 
            "This is a long enough abstract for testing purposes and meets the minimum length requirement of 120 characters that is configured in the preprocessor"
        ], index=[0, 1])
        invalid_indices = preprocessor.get_invalid_indices(abstracts, Mock())
        assert 0 in invalid_indices
        assert 1 not in invalid_indices
    
    def test_get_valid_indices(self, preprocessor):
        abstracts = pd.Series([
            None, 
            "This is a valid abstract with sufficient length for testing purposes and meets the minimum character requirement of 120 characters for the preprocessor"
        ], index=[0, 1])
        valid_indices = preprocessor.get_valid_indices(abstracts, Mock())
        assert 0 not in valid_indices
        assert 1 in valid_indices
    
    def test_process_abstracts_returns_dataframe(self, preprocessor, sample_abstracts_df):
        df_with_long_abstracts = pd.DataFrame({
            'paperId': ['W1', 'W2'],
            'abstract': [
                'This is a valid abstract with sufficient length for testing purposes and meets all the requirements that are needed for proper processing',
                'Another valid abstract with sufficient length for testing purposes and contains enough characters to pass the minimum length validation check'
            ]
        })
        result = preprocessor.process_abstracts(df_with_long_abstracts, Mock())
        assert isinstance(result, pd.DataFrame)
        assert 'valid' in result.columns
        assert 'language' in result.columns