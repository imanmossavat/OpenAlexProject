"""
Fixtures specific to unit tests.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd


# Mock API Provider Fixtures

@pytest.fixture
def mock_api_provider():
    """Create a mock API provider."""
    provider = Mock()
    provider.get_paper = Mock(return_value=None)
    provider.get_papers = Mock(return_value=[])
    provider.get_author_papers = Mock(return_value=([], []))
    provider.failed_paper_ids = []
    provider.inconsistent_api_response_paper_ids = []
    return provider


@pytest.fixture
def mock_openalex_response():
    """Mock OpenAlex API response."""
    return {
        'id': 'https://openalex.org/W2134567890',
        'title': 'Test Paper',
        'abstract_inverted_index': {'test': [0], 'abstract': [1]},
        'publication_year': 2024,
        'doi': 'https://doi.org/10.1234/test',
        'primary_location': {'source': {'display_name': 'Test Venue'}},
        'authorships': [
            {'author': {'id': 'https://openalex.org/A123', 'display_name': 'Test Author'}}
        ],
        'referenced_works': [],
        'cited_by_count': 0
    }


# Mock Services

@pytest.fixture
def mock_retrieval_service():
    """Mock paper retrieval service."""
    service = Mock()
    service.retrieve_papers = Mock(return_value=[])
    service.get_failed_papers = Mock(return_value=[])
    service.get_inconsistent_papers = Mock(return_value=[])
    return service


@pytest.fixture
def mock_validation_service():
    """Mock data validation service."""
    service = Mock()
    service.log_inconsistent_retrievals = Mock()
    service.check_sampler_consistency = Mock()
    service.validate_processed_status = Mock(return_value=True)
    return service


@pytest.fixture
def mock_frame_manager():
    """Mock frame manager with DataFrames."""
    manager = Mock()
    
    # Set up DataFrame properties
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
    
    # Mock methods
    manager.process_data = Mock()
    manager.update_failed_papers = Mock()
    
    return manager


@pytest.fixture
def mock_graph_manager():
    """Mock graph manager."""
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
    """Mock retraction watch manager."""
    manager = Mock()
    manager.process_retracted_papers = Mock(return_value=(pd.DataFrame(), pd.DataFrame()))
    return manager


# Data Store Fixtures

@pytest.fixture
def empty_data_frame_store():
    """Create an empty DataFrameStore."""
    from ArticleCrawler.data.data_frame_store import DataFrameStore
    return DataFrameStore()


@pytest.fixture
def populated_data_frame_store(sample_paper_metadata_df, sample_abstracts_df):
    """Create a DataFrameStore with sample data."""
    from ArticleCrawler.data.data_frame_store import DataFrameStore
    store = DataFrameStore()
    store.df_paper_metadata = sample_paper_metadata_df.copy()
    store.df_abstract = sample_abstracts_df.copy()
    return store


# Validator and Parser Fixtures

@pytest.fixture
def paper_validator(mock_logger):
    """Create a PaperValidator instance."""
    from ArticleCrawler.data.paper_validator import PaperValidator
    return PaperValidator(logger=mock_logger)


@pytest.fixture
def metadata_parser(empty_data_frame_store, mock_logger):
    """Create a MetadataParser instance."""
    from ArticleCrawler.data.metadata_parser import MetadataParser
    from ArticleCrawler.data.frame_manager import AcademicFeatureComputer
    
    feature_computer = AcademicFeatureComputer()
    return MetadataParser(empty_data_frame_store, feature_computer, mock_logger)


@pytest.fixture
def mock_networkx_graph():
    """Mock NetworkX graph."""
    graph = MagicMock()
    graph.nodes = MagicMock(return_value=[])
    graph.edges = MagicMock(return_value=[])
    graph.add_nodes_from = Mock()
    graph.add_edges_from = Mock()
    return graph


@pytest.fixture
def patch_api_sleep(monkeypatch):
    """Patch time.sleep to speed up tests."""
    monkeypatch.setattr('time.sleep', lambda x: None)

@pytest.fixture
def mock_rich_console():
    """Mock rich Console."""
    console = Mock()
    console.print = Mock()
    console.status.return_value.__enter__ = Mock()
    console.status.return_value.__exit__ = Mock()
    return console


@pytest.fixture
def sample_zotero_metadata():
    """Sample Zotero metadata dictionary."""
    return {
        'title': 'Test Paper Title',
        'authors': ['John Doe', 'Jane Smith'],
        'date': '2024-01-15',
        'year': 2024,
        'publication': 'Test Journal',
        'doi': '10.1234/test.2024.001',
        'url': 'https://example.com/paper',
        'abstract': 'This is a test abstract.',
        'tags': ['machine learning', 'AI'],
        'item_type': 'journalArticle',
        'zotero_key': 'ITEM123'
    }


@pytest.fixture
def sample_zotero_collection():
    """Sample Zotero collection."""
    return {
        'key': 'COL123',
        'name': 'Test Collection',
        'data': {
            'key': 'COL123',
            'name': 'Test Collection'
        }
    }


@pytest.fixture
def sample_zotero_item():
    """Sample Zotero item dictionary."""
    return {
        'data': {
            'key': 'ITEM123',
            'title': 'Test Paper Title',
            'creators': [
                {'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'},
                {'creatorType': 'author', 'firstName': 'Jane', 'lastName': 'Smith'}
            ],
            'date': '2024-01-15',
            'publicationTitle': 'Test Journal',
            'DOI': '10.1234/test.2024.001',
            'url': 'https://example.com/paper',
            'abstractNote': 'This is a test abstract.',
            'tags': [{'tag': 'machine learning'}, {'tag': 'AI'}],
            'itemType': 'journalArticle'
        }
    }