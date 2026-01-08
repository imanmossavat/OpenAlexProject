import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, MagicMock
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / "fixtures" / "data"


@pytest.fixture
def mock_logger():
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_paper_object():
    paper = Mock()
    paper.paperId = "W2134567890"
    paper.title = "Sample Research Paper"
    paper.abstract = "This is a sample abstract for testing purposes."
    paper.venue = "Test Conference"
    paper.year = 2024
    paper.doi = "10.1234/test.2024.001"
    author1 = Mock()
    author1.authorId = "A1234567890"
    author1.name = "John Doe"
    author2 = Mock()
    author2.authorId = "A0987654321"
    author2.name = "Jane Smith"
    paper.authors = [author1, author2]
    paper.citations = []
    paper.references = []
    return paper


@pytest.fixture
def sample_paper_without_abstract():
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
    return [sample_paper_object, sample_paper_without_abstract]


@pytest.fixture
def sample_paper_metadata_df():
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
    return pd.DataFrame({
        'paperId': ['W2134567890', 'W9876543210'],
        'abstract': [
            'This is a sample abstract for the first paper.',
            'This is a sample abstract for the second paper.'
        ]
    })


@pytest.fixture
def sample_citations_df():
    return pd.DataFrame({
        'paperId': ['W2134567890', 'W9876543210', 'W1111111111'],
        'citedPaperId': ['W9876543210', 'W1111111111', 'W2134567890']
    })


@pytest.fixture
def sample_api_config():
    from ArticleCrawler.config import APIConfig
    return APIConfig(
        provider_type='openalex',
        retries=3
    )


@pytest.fixture
def sample_sampling_config():
    from ArticleCrawler.config import SamplingConfig
    return SamplingConfig(
        num_papers=5,
        hyper_params={'year': 0.1, 'centrality': 1.0},
        ignored_venues=['ArXiv', 'WWW'],
        no_key_word_lambda=1.0
    )


@pytest.fixture
def sample_text_config():
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
    from ArticleCrawler.config import StorageAndLoggingConfig
    return StorageAndLoggingConfig(
        experiment_file_name='test_experiment',
        root_folder=temp_dir,
        log_level='INFO'
    )


@pytest.fixture
def sample_graph_config():
    from ArticleCrawler.config import GraphConfig
    return GraphConfig(
        ignored_venues=['WWW'],
        include_author_nodes=False,
        max_centrality_iterations=1000
    )


@pytest.fixture
def sample_retraction_config():
    from ArticleCrawler.config import RetractionConfig
    return RetractionConfig(
        enable_retraction_watch=True,
        avoid_retraction_in_sampler=False,
        avoid_retraction_in_reporting=True
    )


@pytest.fixture
def sample_stopping_config():
    from ArticleCrawler.config import StoppingConfig
    return StoppingConfig(
        max_iter=2,
        max_df_size=1000
    )


@pytest.fixture
def sample_seed_papers():
    return ['W2134567890', 'W9876543210']


@pytest.fixture
def sample_keywords():
    return ['machine learning', 'deep learning', 'neural networks']


@pytest.fixture
def assert_dataframe_equals():
    def _assert_equals(df1, df2, check_dtype=True):
        pd.testing.assert_frame_equal(df1, df2, check_dtype=check_dtype)
    return _assert_equals


@pytest.fixture
def mock_requests(monkeypatch):
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
    import numpy as np
    mock_model = Mock()
    mock_model.encode = Mock(return_value=np.random.rand(10, 384))
    mock_model.get_sentence_embedding_dimension = Mock(return_value=384)
    mock_class = Mock(return_value=mock_model)
    monkeypatch.setattr('sentence_transformers.SentenceTransformer', mock_class)
    return mock_model


@pytest.fixture
def integration_test_storage(temp_dir):
    experiment_dir = temp_dir / 'test_experiment'
    experiment_dir.mkdir(parents=True, exist_ok=True)
    (experiment_dir / 'pkl').mkdir(exist_ok=True)
    (experiment_dir / 'log').mkdir(exist_ok=True)
    (experiment_dir / 'vault').mkdir(exist_ok=True)
    (experiment_dir / 'figures').mkdir(exist_ok=True)
    return experiment_dir


@pytest.fixture
def sample_crawler_parameters(sample_seed_papers, sample_keywords):
    from ArticleCrawler.config.crawler_initialization import CrawlerParameters
    return CrawlerParameters(
        seed_paperid=sample_seed_papers,
        keywords=sample_keywords
    )


@pytest.fixture
def integration_configs(temp_dir):
    from tests.fixtures.sample_configs import get_full_config
    return get_full_config(temp_dir)


@pytest.fixture
def mock_api_with_sample_data(sample_papers_list):
    mock_api = Mock()
    mock_api.get_papers = Mock(return_value=sample_papers_list)
    mock_api.get_paper = Mock(side_effect=lambda paper_id: sample_papers_list[0] if paper_id else None)
    mock_api.failed_paper_ids = []
    mock_api.inconsistent_api_response_paper_ids = []
    return mock_api


@pytest.fixture
def mock_pdf_metadata():
    from ArticleCrawler.pdf_processing.models import PDFMetadata
    return PDFMetadata(
        filename="test.pdf",
        title="Test Paper Title",
        doi="10.1234/test.2024.001",
        year="2024",
        authors="John Doe, Jane Smith",
        venue="Test Journal"
    )


@pytest.fixture
def mock_pdf_processing_result(mock_pdf_metadata):
    from ArticleCrawler.pdf_processing.models import PDFProcessingResult
    from pathlib import Path
    return PDFProcessingResult(
        pdf_path=Path("test.pdf"),
        metadata=mock_pdf_metadata,
        success=True
    )


@pytest.fixture
def mock_api_match_result(mock_pdf_metadata):
    from ArticleCrawler.pdf_processing.models import APIMatchResult
    return APIMatchResult(
        metadata=mock_pdf_metadata,
        matched=True,
        paper_id="W123456789",
        confidence=0.95,
        match_method="DOI"
    )


@pytest.fixture
def mock_docker_manager():
    manager = Mock()
    manager.is_grobid_running.return_value = True
    manager.start_container.return_value = True
    manager.stop_container.return_value = True
    manager.is_docker_available.return_value = True
    manager.is_container_running.return_value = False
    return manager


@pytest.fixture
def mock_grobid_client():
    client = Mock()
    client.process_pdfs.return_value = {}
    return client


@pytest.fixture
def mock_metadata_extractor():
    extractor = Mock()
    extractor.extract.return_value = None
    return extractor


@pytest.fixture
def sample_grobid_xml():
    return """<?xml version="1.0"?>
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
        <teiHeader>
            <fileDesc>
                <titleStmt>
                    <title>Test Paper Title</title>
                </titleStmt>
                <sourceDesc>
                    <biblStruct>
                        <analytic>
                            <author>
                                <persName><surname>Doe</surname><forename>John</forename></persName>
                            </author>
                            <idno type="DOI">10.1234/test</idno>
                        </analytic>
                        <monogr>
                            <title level="j">Test Journal</title>
                            <imprint>
                                <date type="published" when="2024">2024</date>
                            </imprint>
                        </monogr>
                    </biblStruct>
                </sourceDesc>
            </fileDesc>
        </teiHeader>
    </TEI>
    """


@pytest.fixture
def mock_rich_console():
    console = Mock()
    console.print = Mock()
    return console


@pytest.fixture
def mock_prompter():
    prompter = Mock()
    prompter.console = Mock()
    prompter.input = Mock(return_value="")
    prompter.input_int = Mock(return_value=0)
    prompter.confirm = Mock(return_value=False)
    prompter.choice = Mock(return_value=0)
    prompter.error = Mock()
    prompter.success = Mock()
    prompter.warning = Mock()
    return prompter


@pytest.fixture
def mock_config_builder():
    from ArticleCrawler.cli.models.experiment_config import ConfigBuilder
    return ConfigBuilder()