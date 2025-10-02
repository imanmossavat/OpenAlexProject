from typing import List, Optional, Union
from pathlib import Path

class TextProcessingConfig:
    """
    Configuration for text processing and NLP operations.
    
    This class handles all text processing settings including preprocessing,
    topic modeling, and visualization parameters.
    """
    
    def __init__(self,
                 # Preprocessing settings
                 abstract_min_length: int = 120,
                 language: str = 'en',
                 special_characters: Optional[List[str]] = None,
                 stopwords: Optional[List[str]] = None,
                 stemmer: Optional[Union[str, object]] = None,
                 
                 # Topic modeling settings
                 num_topics: int = 20,
                 default_topic_model_type: str = 'NMF',
                 top_n_words_per_topic: int = 10,
                 random_state: int = 42,
                 
                 # NMF specific settings
                 nmf_max_iter: int = 1000,
                 
                 # LDA specific settings  
                 lda_max_iter: int = 10,
                 lda_doc_topic_prior: float = 0.8,
                 
                 # Visualization settings
                 save_figures: bool = False,
                 max_rows: int = 4,
                 max_columns: int = 5):
        """
        Initialize text processing configuration.
        
        Args:
            abstract_min_length (int): Minimum length for valid abstracts
            language (str): Language code for text processing
            special_characters (List[str], optional): Patterns for special character removal
            stopwords (List[str], optional): Custom stopwords list
            stemmer (str or object, optional): Stemmer to use ('Porter' or stemmer instance)
            num_topics (int): Number of topics for topic modeling
            default_topic_model_type (str): Default topic model ('NMF' or 'LDA')
            top_n_words_per_topic (int): Number of top words to extract per topic
            random_state (int): Random state for reproducibility
            nmf_max_iter (int): Maximum iterations for NMF
            lda_max_iter (int): Maximum iterations for LDA
            lda_doc_topic_prior (float): Document-topic prior for LDA
            save_figures (bool): Whether to save generated figures
            max_rows (int): Maximum rows in figure grids
            max_columns (int): Maximum columns in figure grids
        """
        # Preprocessing settings
        self.abstract_min_length = abstract_min_length
        self.language = language
        self.special_characters = special_characters or [r'<jats:[^>]+>', r'[^\w\s]']
        
        # Topic modeling settings
        self.num_topics = num_topics
        self.default_topic_model_type = default_topic_model_type
        self.top_n_words_per_topic = top_n_words_per_topic
        self.random_state = random_state
        
        # Model-specific settings
        self.nmf_max_iter = nmf_max_iter
        self.lda_max_iter = lda_max_iter
        self.lda_doc_topic_prior = lda_doc_topic_prior
        
        # Visualization settings
        self.save_figures = save_figures
        self.max_rows = max_rows
        self.max_columns = max_columns
        
        self._initialize_stopwords(stopwords)
        
        self._initialize_stemmer(stemmer)
        
        self._validate_config()
    
    def _initialize_stopwords(self, stopwords: Optional[List[str]]):
        """Initialize stopwords based on language and custom list."""
        if stopwords is None:
            if self.language == 'en':
                try:
                    from nltk.corpus import stopwords as nltk_stopwords
                    self.stopwords = list(nltk_stopwords.words('english'))
                except ImportError:
                    self.stopwords = []
            else:
                self.stopwords = []
        else:
            self.stopwords = stopwords
    
    def _initialize_stemmer(self, stemmer: Optional[Union[str, object]]):
        """Initialize stemmer based on configuration."""
        if stemmer is None:
            self.stemmer = None
        elif stemmer == 'Porter':
            try:
                from nltk.stem import PorterStemmer
                self.stemmer = PorterStemmer()
            except ImportError:
                self.stemmer = None
        else:
            self.stemmer = stemmer
    
    def _validate_config(self):
        """Validate configuration parameters."""
        if self.abstract_min_length < 0:
            raise ValueError("abstract_min_length must be non-negative")
        
        if self.num_topics <= 0:
            raise ValueError("num_topics must be positive")
        
        if self.default_topic_model_type not in ['NMF', 'LDA']:
            raise ValueError("default_topic_model_type must be 'NMF' or 'LDA'")
        
        if self.top_n_words_per_topic <= 0:
            raise ValueError("top_n_words_per_topic must be positive")
    
    def copy(self):
        """Create a copy of this configuration."""
        return TextProcessingConfig(
            abstract_min_length=self.abstract_min_length,
            language=self.language,
            special_characters=self.special_characters.copy(),
            stopwords=self.stopwords.copy() if self.stopwords else None,
            stemmer=self.stemmer,
            num_topics=self.num_topics,
            default_topic_model_type=self.default_topic_model_type,
            top_n_words_per_topic=self.top_n_words_per_topic,
            random_state=self.random_state,
            nmf_max_iter=self.nmf_max_iter,
            lda_max_iter=self.lda_max_iter,
            lda_doc_topic_prior=self.lda_doc_topic_prior,
            save_figures=self.save_figures,
            max_rows=self.max_rows,
            max_columns=self.max_columns
        )

class TextOptions(TextProcessingConfig):
    """Backward compatibility alias for TextProcessingConfig."""
    pass