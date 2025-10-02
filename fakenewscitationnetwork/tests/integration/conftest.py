"""
Fixtures specific to integration tests.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import pandas as pd


@pytest.fixture
def mock_api_provider():
    """Create a mock API provider for integration tests."""
    provider = Mock()
    provider.get_paper = Mock(return_value=None)
    provider.get_papers = Mock(return_value=[])
    provider.get_author_papers = Mock(return_value=([], []))
    provider.failed_paper_ids = []
    provider.inconsistent_api_response_paper_ids = []
    return provider


@pytest.fixture
def mock_frame_manager():
    """Mock frame manager with DataFrames for integration tests."""
    manager = Mock()
    
    manager.df_paper_metadata = pd.DataFrame({
        'paperId': [],
        'doi': [],
        'venue': [],
        'year': [],
        'title': [],
        'processed': [],
        'isSeed': [],
        'isKeyAuthor': [],
        'selected': [],
        'retracted': []
    })
    
    manager.df_abstract = pd.DataFrame(columns=['paperId', 'abstract'])
    manager.df_paper_author = pd.DataFrame(columns=['paperId', 'authorId'])
    manager.df_author = pd.DataFrame(columns=['authorId', 'authorName'])
    manager.df_paper_citations = pd.DataFrame(columns=['paperId', 'citedPaperId'])
    manager.df_paper_references = pd.DataFrame(columns=['paperId', 'referencePaperId'])
    manager.df_citations = pd.DataFrame(columns=['paperId', 'referencePaperId'])
    manager.df_forbidden_entries = pd.DataFrame(columns=['paperId', 'doi', 'reason', 'sampler', 'textProcessing'])
    
    manager.process_data = Mock()
    manager.update_failed_papers = Mock()
    
    return manager


@pytest.fixture
def mock_graph_manager():
    """Mock graph manager for integration tests."""
    manager = Mock()
    manager.DG = Mock()
    manager.update_graph_with_new_nodes = Mock()
    manager.get_paper_centralities = Mock(return_value=pd.DataFrame({
        'paperId': [],
        'centrality (in)': [],
        'centrality (out)': []
    }))
    return manager


@pytest.fixture
def mock_retraction_manager():
    """Mock retraction watch manager for integration tests."""
    manager = Mock()
    manager.process_retracted_papers = Mock(return_value=(pd.DataFrame(), pd.DataFrame()))
    return manager


@pytest.fixture
def integration_data_coordinator(
    mock_api_provider,
    mock_frame_manager,
    mock_graph_manager,
    mock_retraction_manager,
    mock_logger
):
    """
    Create a DataCoordinator with mocked external dependencies
    but real internal logic.
    """
    from ArticleCrawler.data import PaperRetrievalService, DataValidationService, DataCoordinator
    from ArticleCrawler.graph import GraphProcessing
    
    retrieval_service = PaperRetrievalService(mock_api_provider, mock_logger)
    validation_service = DataValidationService(mock_logger)
    
    graph_processing = Mock(spec=GraphProcessing)
    graph_processing.calculate_centrality = Mock()
    
    coordinator = DataCoordinator(
        retrieval_service=retrieval_service,
        validation_service=validation_service,
        frame_manager=mock_frame_manager,
        retraction_manager=mock_retraction_manager,
        graph_manager=mock_graph_manager,
        graph_processing=graph_processing,
        crawl_initial_condition=None,
        logger=mock_logger
    )
    
    return coordinator


@pytest.fixture
def integration_frame_manager(sample_storage_config, mock_logger):
    """
    Create a real FrameManager for integration testing.
    """
    from ArticleCrawler.data import FrameManager
    
    return FrameManager(
        data_storage_options=sample_storage_config,
        logger=mock_logger
    )


@pytest.fixture
def integration_sampler(
    sample_keywords,
    integration_data_coordinator,
    sample_sampling_config,
    sample_storage_config,
    mock_logger
):
    """
    Create a Sampler with real logic but mocked API calls.
    """
    from ArticleCrawler.sampling import Sampler
    
    return Sampler(
        keywords=sample_keywords,
        data_manager=integration_data_coordinator,
        sampling_options=sample_sampling_config,
        logger=mock_logger,
        data_storage_options=sample_storage_config
    )


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests library for API calls."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={})
    mock_response.content = b''
    
    mock_get = Mock(return_value=mock_response)
    mock_post = Mock(return_value=mock_response)
    
    monkeypatch.setattr('requests.get', mock_get)
    monkeypatch.setattr('requests.post', mock_post)
    
    return {'get': mock_get, 'post': mock_post, 'response': mock_response}


@pytest.fixture
def mock_sentence_transformer(monkeypatch):
    """Mock SentenceTransformer for text processing tests."""
    import numpy as np
    
    mock_model = Mock()
    mock_model.encode = Mock(return_value=np.random.rand(10, 384))
    mock_model.get_sentence_embedding_dimension = Mock(return_value=384)
    
    mock_class = Mock(return_value=mock_model)
    monkeypatch.setattr('sentence_transformers.SentenceTransformer', mock_class)
    
    return mock_model


@pytest.fixture
def integration_test_storage(temp_dir):
    """
    Set up test storage structure for integration tests.
    """
    experiment_dir = temp_dir / 'test_experiment'
    experiment_dir.mkdir(parents=True, exist_ok=True)
    
    (experiment_dir / 'pkl').mkdir(exist_ok=True)
    (experiment_dir / 'log').mkdir(exist_ok=True)
    (experiment_dir / 'vault').mkdir(exist_ok=True)
    (experiment_dir / 'figures').mkdir(exist_ok=True)
    
    return experiment_dir


@pytest.fixture
def sample_crawler_parameters(sample_seed_papers, sample_keywords):
    """Create CrawlerParameters for integration testing."""
    from ArticleCrawler.config.crawler_initialization import CrawlerParameters
    
    return CrawlerParameters(
        seed_paperid=sample_seed_papers,
        keywords=sample_keywords
    )


@pytest.fixture
def integration_configs(temp_dir):
    """
    Complete set of configurations for integration testing.
    """
    from tests.fixtures.sample_configs import get_full_config
    return get_full_config(temp_dir)


@pytest.fixture
def mock_api_with_sample_data(sample_papers_list):
    """Mock API that returns sample papers."""
    mock_api = Mock()
    mock_api.get_papers = Mock(return_value=sample_papers_list)
    mock_api.get_paper = Mock(side_effect=lambda paper_id: sample_papers_list[0] if paper_id else None)
    mock_api.failed_paper_ids = []
    mock_api.inconsistent_api_response_paper_ids = []
    return mock_api