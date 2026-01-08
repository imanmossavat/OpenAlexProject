
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from ArticleCrawler.usecases.library_creation import LibraryCreationOrchestrator
from ArticleCrawler.library.models import LibraryConfig, PaperData


@pytest.mark.unit
class TestLibraryCreationOrchestrator:
    
    @pytest.fixture
    def orchestrator(self, mock_logger):
        return LibraryCreationOrchestrator(
            api_provider='openalex',
            logger=mock_logger
        )
    
    @pytest.fixture
    def sample_paper_data(self):
        return PaperData(
            paper_id="W123",
            title="Test Paper",
            authors=[],
            year=2024
        )
    
    def test_create_library(self, orchestrator, sample_paper_data, temp_dir):
        library_path = temp_dir / "test_library"
        
        with patch.object(orchestrator.library_manager, 'create_library_structure'):
            with patch.object(orchestrator.library_manager, 'save_library_config'):
                with patch.object(orchestrator.library_manager, 'get_papers_directory', return_value=library_path / "papers"):
                    with patch.object(orchestrator.api, 'get_paper_as_paper_data', return_value=sample_paper_data):
                        with patch('ArticleCrawler.usecases.library_creation.MarkdownFileGenerator'):
                            config = orchestrator.create_library(
                                library_name="test_library",
                                library_path=library_path,
                                paper_ids=["W123"]
                            )
        
        assert config.name == "test_library"
    
    def test_create_library_with_description(self, orchestrator, temp_dir):
        library_path = temp_dir / "test_library"
        
        with patch.object(orchestrator.library_manager, 'create_library_structure'):
            with patch.object(orchestrator.library_manager, 'save_library_config'):
                with patch.object(orchestrator.library_manager, 'get_papers_directory', return_value=library_path / "papers"):
                    with patch.object(orchestrator, '_fetch_and_save_papers', return_value=0):
                        config = orchestrator.create_library(
                            library_name="test_library",
                            library_path=library_path,
                            paper_ids=[],
                            description="Test description"
                        )
        
        assert config.description == "Test description"
    
    def test_fetch_and_save_papers_success(self, orchestrator, sample_paper_data, temp_dir):
        papers_dir = temp_dir / "papers"
        papers_dir.mkdir()
        
        with patch.object(orchestrator.library_manager, 'get_papers_directory', return_value=papers_dir):
            with patch.object(orchestrator.api, 'get_paper_as_paper_data', return_value=sample_paper_data):
                with patch('ArticleCrawler.usecases.library_creation.MarkdownFileGenerator'):
                    saved_count = orchestrator._fetch_and_save_papers(
                        paper_ids=["W123", "W456"],
                        library_path=temp_dir
                    )
        
        assert saved_count == 2
    
    def test_fetch_and_save_papers_with_failures(self, orchestrator, sample_paper_data, temp_dir):
        papers_dir = temp_dir / "papers"
        papers_dir.mkdir()
        
        with patch.object(orchestrator.library_manager, 'get_papers_directory', return_value=papers_dir):
            with patch.object(orchestrator.api, 'get_paper_as_paper_data', side_effect=[sample_paper_data, None, sample_paper_data]):
                with patch('ArticleCrawler.usecases.library_creation.MarkdownFileGenerator'):
                    saved_count = orchestrator._fetch_and_save_papers(
                        paper_ids=["W123", "W456", "W789"],
                        library_path=temp_dir
                    )
        
        assert saved_count == 2
    
    def test_sanitize_filename(self, orchestrator):
        result = orchestrator._sanitize_filename("Test/Paper:With*Special?Chars")
        
        assert "/" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
    
    def test_sanitize_filename_long_title(self, orchestrator):
        long_title = "A" * 100
        result = orchestrator._sanitize_filename(long_title, max_length=50)
        
        assert len(result) <= 50
    
    def test_create_storage_config(self, orchestrator, temp_dir):
        config = orchestrator._create_storage_config(temp_dir)
        
        assert config.vault_folder == temp_dir
        assert config.abstracts_folder == temp_dir / "papers"
        assert config.open_vault_folder is False