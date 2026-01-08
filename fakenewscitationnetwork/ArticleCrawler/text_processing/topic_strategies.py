import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from sklearn.decomposition import NMF, LatentDirichletAllocation
from typing import Dict, List, Tuple, Any

class TopicModelStrategy(ABC):
    """
    Abstract base class for topic modeling strategies.
    
    This interface defines the contract that all topic modeling implementations
    must follow, enabling easy swapping between different algorithms.
    """
    
    @abstractmethod
    def __init__(self, config):
        """Initialize the strategy with configuration."""
        pass
    
    @abstractmethod
    def fit_transform(self, vectorized_data, feature_names: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict[int, List[str]]]:
        """
        Fit the model and transform the data.
        
        Args:
            vectorized_data: The vectorized text data
            feature_names: List of feature names from vectorizer
            
        Returns:
            Tuple of (topic_matrix, assignments, top_words)
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of this modeling strategy."""
        pass
    
    @abstractmethod
    def get_topic_weights(self) -> np.ndarray:
        """Get topic weights for visualization."""
        pass

class NMFTopicStrategy(TopicModelStrategy):
    """
    Non-negative Matrix Factorization topic modeling strategy.
    
    This strategy implements NMF-based topic modeling with all the existing
    functionality from the original TopicModeling class.
    """
    
    def __init__(self, config):
        """
        Initialize NMF strategy.
        
        Args:
            config: Configuration object with NMF-specific parameters
        """
        self.config = config
        self.model = None
        self.topic_matrix = None
        self.assignments = None
        self.top_words = None
        self.topic_weights = None
    
    def fit_transform(self, vectorized_data, feature_names: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict[int, List[str]]]:
        """
        Fit NMF model and transform the data.
        
        Args:
            vectorized_data: TF-IDF matrix for NMF
            feature_names: List of feature names from TF-IDF vectorizer
            
        Returns:
            Tuple of (topic_matrix, assignments, top_words)
        """
        # Initialize NMF model
        self.model = NMF(
            n_components=self.config.num_topics, 
            random_state=self.config.random_state, 
            max_iter=self.config.nmf_max_iter
        )
        
        # Fit and transform
        self.topic_matrix = self.model.fit_transform(vectorized_data)
        
        # Get topic assignments (highest probability topic for each document)
        self.assignments = np.argmax(self.topic_matrix, axis=1)
        
        # Extract top words for each topic
        self.top_words = self._extract_top_words(feature_names)
        
        # Get topic weights for visualization
        self.topic_weights = self._get_topic_weights()
        
        return self.topic_matrix, self.assignments, self.top_words
    
    def get_model_name(self) -> str:
        """Get the name of this modeling strategy."""
        return "NMF"
    
    def get_topic_weights(self) -> np.ndarray:
        """Get topic weights for visualization."""
        return self.topic_weights
    
    def _extract_top_words(self, feature_names: List[str]) -> Dict[int, List[str]]:
        """Extract top words for each topic."""
        top_words = {}
        top_n = self.config.top_n_words_per_topic
        
        for topic_idx, topic in enumerate(self.model.components_):
            sorted_indices = topic.argsort()[::-1][:top_n]
            top_words[topic_idx] = [feature_names[i] for i in sorted_indices]
            
        return top_words
    
    def _get_topic_weights(self) -> np.ndarray:
        """Get topic weights for visualization."""
        top_n = self.config.top_n_words_per_topic
        return np.array([
            topic[np.argsort(topic)[::-1][:top_n]]
            for topic in self.model.components_
        ])

class LDATopicStrategy(TopicModelStrategy):
    """
    Latent Dirichlet Allocation topic modeling strategy.
    
    This strategy implements LDA-based topic modeling with all the existing
    functionality from the original TopicModeling class.
    """
    
    def __init__(self, config):
        """
        Initialize LDA strategy.
        
        Args:
            config: Configuration object with LDA-specific parameters
        """
        self.config = config
        self.model = None
        self.topic_matrix = None
        self.assignments = None
        self.top_words = None
        self.topic_probs = None
    
    def fit_transform(self, vectorized_data, feature_names: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict[int, List[str]]]:
        """
        Fit LDA model and transform the data.
        
        Args:
            vectorized_data: Count matrix for LDA
            feature_names: List of feature names from count vectorizer
            
        Returns:
            Tuple of (topic_matrix, assignments, top_words)
        """
        # Initialize LDA model
        self.model = LatentDirichletAllocation(
            n_components=self.config.num_topics,
            random_state=self.config.random_state,
            max_iter=self.config.lda_max_iter,
            doc_topic_prior=self.config.lda_doc_topic_prior
        )
        
        # Fit and transform
        self.topic_matrix = self.model.fit_transform(vectorized_data)
        
        # Get topic assignments (highest probability topic for each document)
        self.assignments = np.argmax(self.topic_matrix, axis=1)
        
        # Extract top words for each topic
        self.top_words = self._extract_top_words(feature_names)
        
        # Get topic probabilities for visualization
        self.topic_probs = self._get_topic_weights()
        
        return self.topic_matrix, self.assignments, self.top_words
    
    def get_model_name(self) -> str:
        """Get the name of this modeling strategy."""
        return "LDA"
    
    def get_topic_weights(self) -> np.ndarray:
        """Get topic weights for visualization."""
        return self.topic_probs
    
    def _extract_top_words(self, feature_names: List[str]) -> Dict[int, List[str]]:
        """Extract top words for each topic."""
        top_words = {}
        top_n = self.config.top_n_words_per_topic
        
        for topic_idx, topic in enumerate(self.model.components_):
            sorted_indices = topic.argsort()[::-1][:top_n]
            top_words[topic_idx] = [feature_names[i] for i in sorted_indices]
            
        return top_words
    
    def _get_topic_weights(self) -> np.ndarray:
        """Get topic probabilities for visualization."""
        top_n = self.config.top_n_words_per_topic
        return np.array([
            topic[np.argsort(topic)[::-1][:top_n]]
            for topic in self.model.components_
        ])

class TopicStrategyFactory:
    """
    Factory for creating topic modeling strategies.
    
    This factory encapsulates the logic for selecting and creating
    appropriate topic modeling strategies based on configuration.
    """
    
    @staticmethod
    def create_strategy(model_type: str, config) -> TopicModelStrategy:
        """
        Create a topic modeling strategy.
        
        Args:
            model_type: Type of model ('NMF' or 'LDA')
            config: Configuration object with model parameters
            
        Returns:
            TopicModelStrategy: Instance of the requested strategy
            
        Raises:
            ValueError: If model_type is not supported
        """
        model_type = model_type.upper()
        
        if model_type == 'NMF':
            return NMFTopicStrategy(config)
        elif model_type == 'LDA':
            return LDATopicStrategy(config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}. "
                           f"Supported types: 'NMF', 'LDA'")
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """Get list of available topic modeling strategies."""
        return ['NMF', 'LDA']
    
    @staticmethod
    def get_required_vectorization(model_type: str) -> str:
        """
        Get the required vectorization type for a model.
        
        Args:
            model_type: Type of model ('NMF' or 'LDA')
            
        Returns:
            str: Required vectorization type ('TFIDF' or 'COUNT')
        """
        model_type = model_type.upper()
        
        if model_type == 'NMF':
            return 'TFIDF'
        elif model_type == 'LDA':
            return 'COUNT'
        else:
            raise ValueError(f"Unsupported model type: {model_type}")