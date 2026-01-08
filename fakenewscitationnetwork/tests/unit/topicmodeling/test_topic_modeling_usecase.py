
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from ArticleCrawler.usecases.topic_modeling_usecase import TopicModelingOrchestrator
from ArticleCrawler.library.models import PaperData, TopicCluster


@pytest.mark.unit
class TestTopicModelingOrchestrator:
    
    @pytest.fixture
    def mock_library_manager(self):
        manager = Mock()
        manager.library_exists = Mock(return_value=True)
        manager.load_library_config = Mock()
        manager.get_papers_directory = Mock()
        manager.create_topic_folder = Mock()
        return manager
    
    @pytest.fixture
    def mock_paper_reader(self):
        reader = Mock()
        reader.read_papers_from_directory = Mock()
        return reader
    
    @pytest.fixture
    def mock_topic_labeler(self):
        labeler = Mock()
        labeler.label_clusters = Mock()
        return labeler
    
    @pytest.fixture
    def mock_preprocessor(self):
        preprocessor = Mock()
        preprocessor.process_abstracts = Mock()
        preprocessor.filter_and_stem_abstracts_by_language = Mock()
        return preprocessor
    
    @pytest.fixture
    def mock_vectorizer(self):
        vectorizer = Mock()
        vectorizer.vectorize_and_extract = Mock()
        return vectorizer
    
    @pytest.fixture
    def mock_topic_model(self):
        model = Mock()
        model.apply_topic_modeling = Mock()
        model.results = {}
        return model
    
    @pytest.fixture
    def orchestrator(self, mock_library_manager, mock_paper_reader, mock_topic_labeler, 
                    mock_preprocessor, mock_vectorizer, mock_topic_model, mock_logger):
        return TopicModelingOrchestrator(
            library_manager=mock_library_manager,
            paper_reader=mock_paper_reader,
            topic_labeler=mock_topic_labeler,
            preprocessor=mock_preprocessor,
            vectorizer=mock_vectorizer,
            topic_model=mock_topic_model,
            logger=mock_logger
        )
    
    @pytest.fixture
    def sample_papers(self):
        return [
            PaperData(
                paper_id="W123",
                title="Paper 1",
                authors=[],
                abstract="This is abstract one",
                assigned_topic=0
            ),
            PaperData(
                paper_id="W456",
                title="Paper 2",
                authors=[],
                abstract="This is abstract two",
                assigned_topic=1
            )
        ]
    
    def test_organize_papers_by_topics(self, orchestrator, sample_papers, temp_dir):
        labeled_clusters = [
            TopicCluster(cluster_id=0, label="Topic 1", paper_ids=["W123"]),
            TopicCluster(cluster_id=1, label="Topic 2", paper_ids=["W456"])
        ]
        
        orchestrator.library_manager.create_topic_folder.return_value = temp_dir / "topics" / "Topic 1"
        
        with patch('ArticleCrawler.usecases.topic_modeling_usecase.MarkdownFileGenerator'):
            orchestrator._organize_papers_by_topics(sample_papers, labeled_clusters, temp_dir)
        
        assert orchestrator.library_manager.create_topic_folder.call_count == 2