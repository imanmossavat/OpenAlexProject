import pytest
from ArticleCrawler.config import TextProcessingConfig


@pytest.mark.unit
class TestTextProcessingConfig:
    
    def test_default_initialization(self):
        config = TextProcessingConfig()
        assert config.abstract_min_length == 120
        assert config.language == 'en'
        assert config.num_topics == 20
        assert config.default_topic_model_type == 'NMF'
        assert config.random_state == 42
    
    def test_custom_initialization(self):
        config = TextProcessingConfig(
            abstract_min_length=200,
            language='de',
            num_topics=30,
            default_topic_model_type='LDA',
            random_state=123
        )
        assert config.abstract_min_length == 200
        assert config.language == 'de'
        assert config.num_topics == 30
        assert config.default_topic_model_type == 'LDA'
        assert config.random_state == 123
    
    def test_invalid_abstract_length_raises_error(self):
        with pytest.raises(ValueError, match="abstract_min_length must be non-negative"):
            TextProcessingConfig(abstract_min_length=-1)
    
    def test_invalid_num_topics_raises_error(self):
        with pytest.raises(ValueError, match="num_topics must be positive"):
            TextProcessingConfig(num_topics=0)
    
    def test_invalid_topic_model_type_raises_error(self):
        with pytest.raises(ValueError, match="default_topic_model_type must be"):
            TextProcessingConfig(default_topic_model_type='INVALID')
    
    def test_stemmer_initialization_with_porter(self):
        config = TextProcessingConfig(stemmer='Porter')
        assert config.stemmer is not None
    
    def test_stemmer_initialization_with_none(self):
        config = TextProcessingConfig(stemmer=None)
        assert config.stemmer is None
    
    def test_stopwords_initialization_english(self):
        config = TextProcessingConfig(language='en')
        assert isinstance(config.stopwords, list)
    
    def test_copy_creates_independent_instance(self):
        config1 = TextProcessingConfig(num_topics=20)
        config2 = config1.copy()
        config2.num_topics = 30
        assert config1.num_topics == 20
        assert config2.num_topics == 30 
