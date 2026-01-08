 
"""
Sample configuration objects for testing.
"""

from pathlib import Path
from ArticleCrawler.config import (
    APIConfig, SamplingConfig, TextProcessingConfig,
    StorageAndLoggingConfig, GraphConfig, RetractionConfig, StoppingConfig
)


def get_minimal_config(temp_dir: Path = None):
    """
    Get minimal configuration for basic testing.
    
    Args:
        temp_dir: Temporary directory for storage
    
    Returns:
        Dictionary of minimal config objects
    """
    temp_dir = temp_dir or Path('/tmp/test_crawler')
    
    return {
        'api_config': APIConfig(provider_type='openalex', retries=1),
        'sampling_config': SamplingConfig(num_papers=1),
        'text_config': TextProcessingConfig(),
        'storage_config': StorageAndLoggingConfig(
            experiment_file_name='test',
            root_folder=temp_dir
        ),
        'graph_config': GraphConfig(),
        'retraction_config': RetractionConfig(),
        'stopping_config': StoppingConfig(max_iter=1)
    }


def get_full_config(temp_dir: Path = None):
    """
    Get complete configuration with all options.
    
    Args:
        temp_dir: Temporary directory for storage
    
    Returns:
        Dictionary of full config objects
    """
    temp_dir = temp_dir or Path('/tmp/test_crawler')
    
    return {
        'api_config': APIConfig(
            provider_type='openalex',
            retries=3
        ),
        'sampling_config': SamplingConfig(
            num_papers=10,
            hyper_params={'year': 0.3, 'centrality': 1.0},
            ignored_venues=['ArXiv', 'WWW'],
            no_key_word_lambda=0.2
        ),
        'text_config': TextProcessingConfig(
            abstract_min_length=120,
            num_topics=20,
            default_topic_model_type='NMF',
            language='en',
            save_figures=True,
            random_state=42
        ),
        'storage_config': StorageAndLoggingConfig(
            experiment_file_name='full_test',
            root_folder=temp_dir,
            log_level='DEBUG'
        ),
        'graph_config': GraphConfig(
            ignored_venues=['WWW'],
            include_author_nodes=True,
            max_centrality_iterations=1000
        ),
        'retraction_config': RetractionConfig(
            enable_retraction_watch=True,
            avoid_retraction_in_sampler=True,
            avoid_retraction_in_reporting=True
        ),
        'stopping_config': StoppingConfig(
            max_iter=5,
            max_df_size=10000
        )
    }