import pytest
import pandas as pd
from unittest.mock import Mock


@pytest.mark.integration
class TestTextProcessingPipeline:
    
    def test_preprocessing_to_vectorization(self, sample_text_config):
        from ArticleCrawler.text_processing.preprocessing import TextPreProcessing
        from ArticleCrawler.text_processing.vectorization import TextTransformation
        
        preprocessor = TextPreProcessing(config=sample_text_config)
        transformer = TextTransformation(config=sample_text_config)
        
        df = pd.DataFrame({
            'paperId': ['W1', 'W2'],
            'abstract': [
                'This is a test abstract with sufficient length for processing.',
                'Another test abstract with machine learning content.'
            ]
        })
        
        processed_df = preprocessor.process_abstracts(df, Mock())
        
        if len(processed_df[processed_df['valid']]) > 0:
            vectorizer, matrix, features = transformer.vectorize_and_extract(
                processed_df[processed_df['valid']],
                Mock(),
                model_type='TFIDF'
            )
            assert matrix is not None
            assert len(features) > 0 
