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
    provider.get_author_papers = Mock(return_value=([], [], None))
    provider.get_venue_papers = Mock(return_value=([], [], None))
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


@pytest.fixture
def sample_temporal_data():
    from ArticleCrawler.library.models import TemporalTopicData, TimePeriod
    
    periods = [
        TimePeriod(start_year=2020, end_year=2022),
        TimePeriod(start_year=2023, end_year=2025)
    ]
    
    return TemporalTopicData(
        author_id="A123456",
        author_name="Test Author",
        time_periods=periods,
        topic_labels=["Machine Learning", "Deep Learning", "Neural Networks"],
        topic_distributions=[
            [0.5, 0.3, 0.2],
            [0.3, 0.4, 0.3]
        ],
        paper_counts_per_period=[10, 8],
        total_papers=18,
        papers_by_period={
            "2020-2022": ["W1", "W2", "W3"],
            "2023-2025": ["W4", "W5"]
        }
    )


@pytest.fixture
def sample_author_info():
    from ArticleCrawler.library.models import AuthorInfo
    
    return AuthorInfo(
        id="A123456789",
        name="Dr. Test Researcher",
        works_count=50,
        cited_by_count=500,
        institutions=["Test University"],
        orcid="0000-0000-0000-0000"
    )


@pytest.fixture
def sample_time_periods():
    from ArticleCrawler.library.models import TimePeriod
    
    return [
        TimePeriod(start_year=2020, end_year=2022),
        TimePeriod(start_year=2023, end_year=2025),
        TimePeriod(start_year=2026, end_year=2028)
    ]


@pytest.fixture
def sample_papers_with_topics():
    from ArticleCrawler.library.models import PaperData
    
    papers = []
    topics = ["Machine Learning", "Deep Learning", "Neural Networks"]
    years = [2020, 2021, 2022, 2023, 2024, 2025]
    
    for i, year in enumerate(years):
        for j in range(2):
            papers.append(PaperData(
                paper_id=f"W{i*2+j}",
                title=f"Research Paper {i*2+j}",
                year=year,
                authors=[{"authorId": "A123", "name": "Test Author"}],
                abstract=f"Abstract for paper {i*2+j}",
                topic_label=topics[i % 3]
            ))
    
    return papers


@pytest.fixture
def mock_topic_orchestrator():
    orchestrator = Mock()
    orchestrator.run.return_value = Mock()
    return orchestrator


@pytest.fixture
def mock_temporal_analyzer():
    from ArticleCrawler.library.models import TemporalTopicData, TimePeriod
    
    analyzer = Mock()
    periods = [TimePeriod(start_year=2020, end_year=2022)]
    analyzer.analyze_evolution.return_value = TemporalTopicData(
        author_id="A123",
        author_name="Test",
        time_periods=periods,
        topic_labels=["Topic1", "Topic2"],
        topic_distributions=[[0.6, 0.4]],
        paper_counts_per_period=[5],
        total_papers=5,
        papers_by_period={}
    )
    return analyzer


@pytest.fixture
def mock_visualizer(temp_dir):
    visualizer = Mock()
    visualizer.visualize.return_value = None
    return visualizer


@pytest.fixture
def mock_temp_library_manager(temp_dir):
    manager = Mock()
    manager.create_temp_library.return_value = temp_dir / "temp_lib"
    manager.cleanup_temp_library.return_value = True
    manager.make_permanent.return_value = temp_dir / "permanent_lib"
    return manager


@pytest.fixture
def mock_author_search_service():
    from ArticleCrawler.library.models import AuthorInfo, PaperData
    
    service = Mock()
    service.search_authors.return_value = [
        AuthorInfo(id="A1", name="Author One", works_count=30),
        AuthorInfo(id="A2", name="Author Two", works_count=20)
    ]
    service.get_author_papers.return_value = [
        PaperData(paper_id="W1", title="Paper 1", year=2020, authors=[]),
        PaperData(paper_id="W2", title="Paper 2", year=2021, authors=[])
    ]
    return service


@pytest.fixture
def temporal_config():
    from ArticleCrawler.config.temporal_config import TemporalAnalysisConfig
    
    return TemporalAnalysisConfig(
        time_period_years=3,
        min_papers_per_period=2,
        min_papers_total=5,
        period_strategy="fixed"
    )


@pytest.fixture
def visualization_config():
    from ArticleCrawler.visualization.visualization_config import VisualizationConfig
    
    return VisualizationConfig(
        figure_width=12,
        figure_height=8,
        dpi=300,
        show_grid=True
    )

@pytest.fixture
def mock_author_search_service():
    from ArticleCrawler.library.models import AuthorInfo, PaperData
    
    service = Mock()
    service.search_authors.return_value = [
        AuthorInfo(id="A1", name="Author One", works_count=30, cited_by_count=300),
        AuthorInfo(id="A2", name="Author Two", works_count=20, cited_by_count=200)
    ]
    service.fetch_author_papers.return_value = [
        PaperData(paper_id="W1", title="Paper 1", year=2020, authors=[]),
        PaperData(paper_id="W2", title="Paper 2", year=2021, authors=[])
    ]
    service.select_best_author.return_value = AuthorInfo(
        id="A1", name="Author One", works_count=30, cited_by_count=300
    )
    return service
