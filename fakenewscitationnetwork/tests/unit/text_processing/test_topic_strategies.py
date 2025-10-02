 
import pytest
import numpy as np
from ArticleCrawler.text_processing.topic_strategies import (
    NMFTopicStrategy, LDATopicStrategy, TopicStrategyFactory
)


@pytest.mark.unit
class TestTopicStrategyFactory:
    
    def test_create_nmf_strategy(self, sample_text_config):
        strategy = TopicStrategyFactory.create_strategy('NMF', sample_text_config)
        assert isinstance(strategy, NMFTopicStrategy)
    
    def test_create_lda_strategy(self, sample_text_config):
        strategy = TopicStrategyFactory.create_strategy('LDA', sample_text_config)
        assert isinstance(strategy, LDATopicStrategy)
    
    def test_invalid_model_type_raises_error(self, sample_text_config):
        with pytest.raises(ValueError, match="Unsupported model type"):
            TopicStrategyFactory.create_strategy('INVALID', sample_text_config)
    
    def test_get_available_strategies(self):
        strategies = TopicStrategyFactory.get_available_strategies()
        assert 'NMF' in strategies
        assert 'LDA' in strategies
    
    def test_get_required_vectorization_nmf(self):
        vectorization = TopicStrategyFactory.get_required_vectorization('NMF')
        assert vectorization == 'TFIDF'
    
    def test_get_required_vectorization_lda(self):
        vectorization = TopicStrategyFactory.get_required_vectorization('LDA')
        assert vectorization == 'COUNT'


@pytest.mark.unit
class TestNMFTopicStrategy:
    
    @pytest.fixture
    def nmf_strategy(self, sample_text_config):
        return NMFTopicStrategy(sample_text_config)
    
    def test_initialization(self, nmf_strategy):
        assert nmf_strategy.model is None
        assert nmf_strategy.topic_matrix is None
    
    def test_get_model_name(self, nmf_strategy):
        assert nmf_strategy.get_model_name() == 'NMF'
    
    def test_fit_transform_with_sample_data(self, nmf_strategy):
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        texts = [
            'machine learning artificial intelligence',
            'deep learning neural networks',
            'natural language processing'
        ]
        vectorizer = TfidfVectorizer()
        vectorized_data = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        topic_matrix, assignments, top_words = nmf_strategy.fit_transform(
            vectorized_data, feature_names
        )
        
        assert topic_matrix is not None
        assert len(assignments) == len(texts)
        assert len(top_words) > 0


@pytest.mark.unit
class TestLDATopicStrategy:
    
    @pytest.fixture
    def lda_strategy(self, sample_text_config):
        return LDATopicStrategy(sample_text_config)
    
    def test_initialization(self, lda_strategy):
        assert lda_strategy.model is None
        assert lda_strategy.topic_matrix is None
    
    def test_get_model_name(self, lda_strategy):
        assert lda_strategy.get_model_name() == 'LDA'
    
    def test_fit_transform_with_sample_data(self, lda_strategy):
        from sklearn.feature_extraction.text import CountVectorizer
        
        texts = [
            'machine learning artificial intelligence',
            'deep learning neural networks',
            'natural language processing'
        ]
        vectorizer = CountVectorizer()
        vectorized_data = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        topic_matrix, assignments, top_words = lda_strategy.fit_transform(
            vectorized_data, feature_names
        )
        
        assert topic_matrix is not None
        assert len(assignments) == len(texts)
        assert len(top_words) > 0