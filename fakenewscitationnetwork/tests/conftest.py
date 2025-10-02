"""
Global test fixtures available to all test modules.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, MagicMock
import tempfile
import shutil


# Directory and Path Fixtures

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "fixtures" / "data"


# Mock Logger Fixture

@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


# Sample Paper Objects

@pytest.fixture
def sample_paper_object():
    """Create a sample paper object with all attributes."""
    paper = Mock()
    paper.paperId = "W2134567890"
    paper.title = "Sample Research Paper"
    paper.abstract = "This is a sample abstract for testing purposes."
    paper.venue = "Test Conference"
    paper.year = 2024
    paper.doi = "10.1234/test.2024.001"
    
    # Authors
    author1 = Mock()
    author1.authorId = "A1234567890"
    author1.name = "John Doe"
    
    author2 = Mock()
    author2.authorId = "A0987654321"
    author2.name = "Jane Smith"
    
    paper.authors = [author1, author2]
    
    # Citations and references (empty for basic fixture)
    paper.citations = []
    paper.references = []
    
    return paper


@pytest.fixture
def sample_paper_without_abstract():
    """Create a sample paper object without abstract (common in OpenAlex)."""
    paper = Mock()
    paper.paperId = "W9876543210"
    paper.title = "Paper Without Abstract"
    paper.abstract = None
    paper.venue = "Test Journal"
    paper.year = 2023
    paper.doi = "10.1234/test.2023.002"
    
    author = Mock()
    author.authorId = "A5555555555"
    author.name = "Test Author"
    
    paper.authors = [author]
    paper.citations = []
    paper.references = []
    
    return paper


@pytest.fixture
def sample_papers_list(sample_paper_object, sample_paper_without_abstract):
    """List of sample papers for batch testing."""
    return [sample_paper_object, sample_paper_without_abstract]


# Sample DataFrames

@pytest.fixture
def sample_paper_metadata_df():
    """Sample paper metadata DataFrame."""
    return pd.DataFrame({
        'paperId': ['W2134567890', 'W9876543210', 'W1111111111'],
        'doi': ['10.1234/test.001', '10.1234/test.002', '10.1234/test.003'],
        'venue': ['Test Conference', 'Test Journal', 'Workshop'],
        'year': [2024, 2023, 2022],
        'title': ['Paper One', 'Paper Two', 'Paper Three'],
        'processed': [True, True, False],
        'isSeed': [True, False, False],
        'isKeyAuthor': [False, False, False],
        'selected': [True, False, False],
        'retracted': [False, False, False]
    })


@pytest.fixture
def sample_abstracts_df():
    """Sample abstracts DataFrame."""
    return pd.DataFrame({
        'paperId': ['W2134567890', 'W9876543210'],
        'abstract': [
            'This is a sample abstract for the first paper.',
            'This is a sample abstract for the second paper.'
        ]
    })


@pytest.fixture
def sample_citations_df():
    """Sample citations DataFrame."""
    return pd.DataFrame({
        'paperId': ['W2134567890', 'W9876543210', 'W1111111111'],
        'citedPaperId': ['W9876543210', 'W1111111111', 'W2134567890']
    })


# Configuration Objects

@pytest.fixture
def sample_api_config():
    """Sample API configuration."""
    from ArticleCrawler.config import APIConfig
    return APIConfig(
        provider_type='openalex',
        retries=3
    )


@pytest.fixture
def sample_sampling_config():
    """Sample sampling configuration."""
    from ArticleCrawler.config import SamplingConfig
    return SamplingConfig(
        num_papers=5,
        hyper_params={'year': 0.1, 'centrality': 1.0},
        ignored_venues=['ArXiv', 'WWW'],
        no_key_word_lambda=1.0
    )


@pytest.fixture
def sample_text_config():
    """Sample text processing configuration."""
    from ArticleCrawler.config import TextProcessingConfig
    return TextProcessingConfig(
        abstract_min_length=120,
        language='en',
        num_topics=20,
        default_topic_model_type='NMF',
        random_state=42
    )


@pytest.fixture
def sample_storage_config(temp_dir):
    """Sample storage configuration."""
    from ArticleCrawler.config import StorageAndLoggingConfig
    return StorageAndLoggingConfig(
        experiment_file_name='test_experiment',
        root_folder=temp_dir,
        log_level='INFO'
    )


@pytest.fixture
def sample_graph_config():
    """Sample graph configuration."""
    from ArticleCrawler.config import GraphConfig
    return GraphConfig(
        ignored_venues=['WWW'],
        include_author_nodes=False,
        max_centrality_iterations=1000
    )


@pytest.fixture
def sample_retraction_config():
    """Sample retraction configuration."""
    from ArticleCrawler.config import RetractionConfig
    return RetractionConfig(
        enable_retraction_watch=True,
        avoid_retraction_in_sampler=False,
        avoid_retraction_in_reporting=True
    )


@pytest.fixture
def sample_stopping_config():
    """Sample stopping configuration."""
    from ArticleCrawler.config import StoppingConfig
    return StoppingConfig(
        max_iter=2,
        max_df_size=1000
    )


# Seed Data

@pytest.fixture
def sample_seed_papers():
    """Sample seed paper IDs."""
    return ['W2134567890', 'W9876543210']


@pytest.fixture
def sample_keywords():
    """Sample keyword filters."""
    return ['machine learning', 'deep learning', 'neural networks']


# Test Utilities

@pytest.fixture
def assert_dataframe_equals():
    """Utility function to compare DataFrames."""
    def _assert_equals(df1, df2, check_dtype=True):
        pd.testing.assert_frame_equal(df1, df2, check_dtype=check_dtype)
    return _assert_equals