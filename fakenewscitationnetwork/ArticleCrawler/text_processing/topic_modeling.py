import os
from math import ceil
from pathlib import Path
from typing import List, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .topic_strategies import TopicStrategyFactory, TopicModelStrategy
from .visualization import TopicVisualization

class TopicModeling:
    """
    Topic modeling coordinator using the Strategy pattern.
    
    This class coordinates topic modeling operations by delegating to specific
    strategy implementations. It maintains all existing functionality while
    providing a clean separation between different algorithms.
    """
    
    def __init__(self, config):
        """
        Initialize topic modeling coordinator.
        
        Args:
            config: Configuration object with topic modeling parameters
        """
        self.config = config
        self.strategies = {}  # Cache for strategy instances
        self.results = {}     # Storage for model results
        self._visualization = TopicVisualization(config=config)

    def set_companion_writer(self, writer):
        if hasattr(self._visualization, "set_companion_writer"):
            self._visualization.set_companion_writer(writer)

    def apply_topic_modeling(self, transformation_instance, logger, model_type: Optional[str] = None):
        """
        Apply topic modeling using the specified strategy.
        
        Args:
            transformation_instance: Object containing vectorized data
            logger: Logger for progress tracking
            model_type: Type of model to use ('NMF' or 'LDA')
        """
        # Use default model type if none specified
        if model_type is None:
            model_type = self.config.default_topic_model_type
            
        logger.info(f"Applying topic modeling with model type: {model_type}")

        # Get required vectorization type and data
        vectorization_type = TopicStrategyFactory.get_required_vectorization(model_type)
        vectorized_data, feature_names = self._get_vectorization_data(
            transformation_instance, vectorization_type
        )

        if vectorized_data is None or feature_names is None:
            logger.error("Vectorized data or feature names are missing from the transformation instance.")
            raise ValueError("Vectorized data or feature names are not populated in the transformation instance.")

        # Create or get strategy
        strategy = self._get_strategy(model_type)
        
        # Apply topic modeling
        logger.info(f"Fitting the model: {model_type}")
        topic_matrix, assignments, top_words = strategy.fit_transform(vectorized_data, feature_names)
        
        # Store results
        self.results[model_type] = {
            'strategy': strategy,
            'topic_matrix': topic_matrix,
            'assignments': assignments,
            'top_words': top_words,
            'topic_weights': strategy.get_topic_weights()
        }
        
        logger.info(f"Topic modeling completed for {model_type}.")

    def _get_strategy(self, model_type: str) -> TopicModelStrategy:
        """Get or create a strategy instance."""
        if model_type not in self.strategies:
            self.strategies[model_type] = TopicStrategyFactory.create_strategy(model_type, self.config)
        return self.strategies[model_type]

    def _get_vectorization_data(self, transformation_instance, vectorization_type: str):
        """Get the appropriate vectorized data based on model requirements."""
        if vectorization_type == 'TFIDF':
            return transformation_instance.tfidf_matrix, transformation_instance.tfidf_feature_names
        elif vectorization_type == 'COUNT':
            return transformation_instance.count_matrix, transformation_instance.count_feature_names
        else:
            raise ValueError(f"Unsupported vectorization type: {vectorization_type}")

    def add_topic_columns(self, df: pd.DataFrame, model_type: str, logger) -> pd.DataFrame:
        """
        Add topic assignment columns to a DataFrame.
        
        Args:
            df: DataFrame to add columns to
            model_type: Type of model used
            logger: Logger for progress tracking
            
        Returns:
            DataFrame with added topic columns
        """
        logger.info(f"Adding topic columns for {model_type} to the DataFrame.")
        
        if model_type not in self.results:
            logger.error(f"No results found for model type: {model_type}")
            return df
        
        # Get valid indices (papers that were processed)
        language = self.config.language
        valid_indices = df[df['valid'] & (df['language'] == language)].index
        
        # Get assignments
        assignments = self.results[model_type]['assignments']
        
        # Add topic column
        column_name = f'{model_type.lower()}_topic'
        df[column_name] = -1  # Default value for unprocessed papers
        df.loc[valid_indices, column_name] = assignments
        
        return df

    def check_model(self, model_type: str, logger) -> bool:
        """
        Check if a model has been fitted and is available.
        
        Args:
            model_type: Type of model to check
            logger: Logger for status messages
            
        Returns:
            bool: True if model is available, False otherwise
        """
        if model_type in self.results:
            return True
        else:
            logger.info(f"No fitted model found for type: {model_type}")
            return False

    # Visualization methods (delegate to visualization component)
    def visualize_word_cloud(self, logger, figure_folder=None, timestamp_final_pkl=None, model_type: Optional[str] = None):
        """Generate word clouds for topic visualization."""
        model_type = model_type or self.config.default_topic_model_type
        
        if not self.check_model(model_type, logger):
            logger.error(f"Cannot visualize: No model results for {model_type}")
            return
            
        results = self.results[model_type]
        
        try:
            save_dir = self._get_save_directory(figure_folder, timestamp_final_pkl, logger)
            self._visualization.word_cloud(
                words=results['top_words'], 
                topic_weights=results['topic_weights'],
                model_type=model_type,
                logger=logger,
                save_dir=save_dir
            )
        except Exception as e:
            logger.error(f"Error generating word clouds: {e}")

    def visualize_top_words_barplot(self, logger, figure_folder=None, timestamp_final_pkl=None, model_type: Optional[str] = None):
        """Generate bar plots for top words visualization."""
        model_type = model_type or self.config.default_topic_model_type
        
        if not self.check_model(model_type, logger):
            logger.error(f"Cannot visualize: No model results for {model_type}")
            return
            
        results = self.results[model_type]
        
        try:
            save_dir = self._get_save_directory(figure_folder, timestamp_final_pkl, logger)
            self._visualization.top_words_barplot(
                words=results['top_words'], 
                topic_weights=results['topic_weights'],
                model_type=model_type,
                logger=logger,
                save_dir=save_dir
            )
        except Exception as e:
            logger.error(f"Error generating bar plots: {e}")

    def visualize_temporal_topic_evolution(self, df: pd.DataFrame, logger, figure_folder=None, timestamp_final_pkl=None, model_type: Optional[str] = None):
        """Generate temporal topic evolution visualization."""
        model_type = model_type or self.config.default_topic_model_type
        
        if not self.check_model(model_type, logger):
            logger.error(f"Cannot visualize: No model results for {model_type}")
            return
            
        try:
            save_dir = self._get_save_directory(figure_folder, timestamp_final_pkl, logger)
            self._visualization.temporal_topic_area_chart(
                df, 
                model_type=model_type,
                logger=logger,
                save_dir=save_dir
            )
        except Exception as e:
            logger.error(f"Error generating temporal visualization: {e}")

    def _get_save_directory(self, figure_folder, timestamp_final_pkl, logger):
        """Get the directory for saving figures."""
        try:
            if self.config.save_figures and figure_folder and timestamp_final_pkl:
                save_dir = Path(figure_folder) / timestamp_final_pkl
                os.makedirs(save_dir, exist_ok=True)
                return save_dir
            elif figure_folder:
                return Path(figure_folder)
            else:
                return None
        except (AttributeError, Exception) as e:
            logger.error(f"Error setting save_dir: {str(e)}")
            return Path(figure_folder) if figure_folder else None

    # Backward compatibility properties
    @property
    def nmf_assignments(self):
        """Backward compatibility for NMF assignments."""
        return self.results.get('NMF', {}).get('assignments')
    
    @property
    def nmf_top_words(self):
        """Backward compatibility for NMF top words."""
        return self.results.get('NMF', {}).get('top_words')
    
    @property
    def nmf_topic_weights(self):
        """Backward compatibility for NMF topic weights."""
        return self.results.get('NMF', {}).get('topic_weights')
    
    @property
    def lda_assignments(self):
        """Backward compatibility for LDA assignments."""
        return self.results.get('LDA', {}).get('assignments')
    
    @property
    def lda_top_words(self):
        """Backward compatibility for LDA top words."""
        return self.results.get('LDA', {}).get('top_words')
    
    @property
    def lda_topic_probs(self):
        """Backward compatibility for LDA topic probabilities."""
        return self.results.get('LDA', {}).get('topic_weights')
