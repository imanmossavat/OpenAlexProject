import pytest
import pandas as pd
from unittest.mock import Mock, patch
from ArticleCrawler.text_processing.topic_modeling import TopicModeling


@pytest.mark.unit
class TestTopicModeling:
    
    @pytest.fixture
    def topic_modeling(self, sample_text_config):
        return TopicModeling(sample_text_config)
    
    def test_initialization(self, topic_modeling):
        assert topic_modeling.config is not None
        assert topic_modeling.strategies == {}
        assert topic_modeling.results == {}
    
    def test_check_model_returns_false_for_unfitted_model(self, topic_modeling):
        result = topic_modeling.check_model('NMF', Mock())
        assert result == False
    
    def test_add_topic_columns_adds_column_to_dataframe(self, topic_modeling):
        df = pd.DataFrame({'paperId': ['W1', 'W2'], 'valid': [True, True], 'language': ['en', 'en']})
        topic_modeling.results['NMF'] = {
            'assignments': [0, 1],
            'top_words': {},
            'topic_weights': None
        }
        
        result = topic_modeling.add_topic_columns(df, 'NMF', Mock())
        assert 'nmf_topic' in result.columns
    
    def test_add_topic_columns_sets_default_for_invalid_papers(self, topic_modeling):
        df = pd.DataFrame({'paperId': ['W1', 'W2'], 'valid': [True, False], 'language': ['en', 'en']})
        topic_modeling.results['NMF'] = {
            'assignments': [0],
            'top_words': {},
            'topic_weights': None
        }
        
        result = topic_modeling.add_topic_columns(df, 'NMF', Mock())
        assert result.loc[1, 'nmf_topic'] == -1 
