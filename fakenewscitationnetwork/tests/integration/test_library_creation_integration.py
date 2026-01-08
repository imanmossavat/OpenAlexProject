
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, call
from ArticleCrawler.usecases.library_creation import LibraryCreationOrchestrator
from ArticleCrawler.library.library_manager import LibraryManager
from ArticleCrawler.library.models import PaperData


@pytest.mark.integration
class TestLibraryCreationIntegration:
    
    @pytest.fixture
    def library_manager(self, mock_logger):
        return LibraryManager(logger=mock_logger)
    
    @pytest.fixture
    def orchestrator(self, mock_logger):
        return LibraryCreationOrchestrator(
            api_provider='openalex',
            logger=mock_logger
        )
    
    @pytest.fixture
    def sample_paper_data(self):
        return PaperData(
            paper_id="W2134567890",
            title="Integration Test Paper",
            authors=[
                {'authorId': 'A123', 'name': 'Test Author'}
            ],
            year=2024,
            venue="Test Venue",
            abstract="Test abstract for integration testing.",
            concepts=[
                {'id': 'C123', 'display_name': 'Machine Learning', 'level': 2, 'score': 0.9}
            ]
        )
    
    def test_create_library_full_workflow(self, orchestrator, sample_paper_data, temp_dir):
        library_path = temp_dir / "integration_library"
        
        with patch.object(orchestrator.api, 'get_paper_as_paper_data', return_value=sample_paper_data):
            config = orchestrator.create_library(
                library_name="integration_library",
                library_path=library_path,
                paper_ids=["W2134567890"],
                description="Integration test library"
            )
        
        assert config.name == "integration_library"
        assert library_path.exists()
        assert (library_path / "library_config.yaml").exists()
        assert (library_path / "papers").exists()
    
    def test_create_library_with_multiple_papers(self, orchestrator, sample_paper_data, temp_dir):
        library_path = temp_dir / "multi_paper_library"
        
        mock_get_paper = Mock(return_value=sample_paper_data)
        with patch.object(orchestrator.api, 'get_paper_as_paper_data', mock_get_paper):
            config = orchestrator.create_library(
                library_name="multi_paper_library",
                library_path=library_path,
                paper_ids=["W123", "W456", "W789"]
            )
        
        assert config.name == "multi_paper_library"
        assert mock_get_paper.call_count == 3
    
    def test_create_library_handles_api_failures(self, orchestrator, sample_paper_data, temp_dir):
        library_path = temp_dir / "failure_library"
        
        with patch.object(orchestrator.api, 'get_paper_as_paper_data', side_effect=[
            sample_paper_data,
            None,
            sample_paper_data
        ]):
            config = orchestrator.create_library(
                library_name="failure_library",
                library_path=library_path,
                paper_ids=["W123", "W456", "W789"]
            )
        
        assert config.name == "failure_library"
        assert library_path.exists()