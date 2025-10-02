 
import pytest
from unittest.mock import Mock
import pandas as pd
from ArticleCrawler.text_processing.vectorization import TextTransformation


@pytest.mark.unit
class TestTextTransformation:
    
    @pytest.fixture
    def transformer(self, sample_text_config):
        return TextTransformation(config=sample_text_config)
    
    def test_initialization(self, transformer):
        assert transformer.config is not None
        assert transformer.tfidf_matrix is None
        assert transformer.count_matrix is None
    
    def test_vectorize_and_extract_tfidf(self, transformer):
        df = pd.DataFrame({
            'abstract': [
                'machine learning artificial intelligence',
                'deep learning neural networks',
                'natural language processing'
            ]
        })
        vectorizer, matrix, features = transformer.vectorize_and_extract(df, Mock(), model_type='TFIDF')
        
        assert vectorizer is not None
        assert matrix is not None
        assert len(features) > 0
        assert transformer.tfidf_matrix is not None
    
    def test_vectorize_and_extract_count(self, transformer):
        df = pd.DataFrame({
            'abstract': [
                'machine learning artificial intelligence',
                'deep learning neural networks'
            ]
        })
        vectorizer, matrix, features = transformer.vectorize_and_extract(df, Mock(), model_type='COUNT')
        
        assert vectorizer is not None
        assert matrix is not None
        assert transformer.count_matrix is not None
    
    def test_invalid_model_type_raises_error(self, transformer):
        df = pd.DataFrame({'abstract': ['test text']})
        with pytest.raises(ValueError, match="Invalid model_type"):
            transformer.vectorize_and_extract(df, Mock(), model_type='INVALID')