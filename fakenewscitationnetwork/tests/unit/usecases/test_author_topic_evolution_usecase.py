import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from ArticleCrawler.usecases.author_topic_evolution_usecase import AuthorTopicEvolutionUseCase
from ArticleCrawler.library.models import AuthorInfo, PaperData, TemporalTopicData, TimePeriod


class TestAuthorTopicEvolutionUseCase:
    
    @pytest.fixture
    def mock_dependencies(self, mock_logger, temp_dir):
        return {
            'api_provider': Mock(),
            'author_search_service': Mock(),
            'library_manager': Mock(),
            'topic_orchestrator': Mock(),
            'temporal_analyzer': Mock(),
            'visualizer': Mock(),
            'temp_library_manager': Mock(),
            'markdown_writer': Mock(),
            'logger': mock_logger
        }
    
    @pytest.fixture
    def use_case(self, mock_dependencies):
        return AuthorTopicEvolutionUseCase(**mock_dependencies)
    
    @pytest.fixture
    def sample_author(self):
        return AuthorInfo(id="A123", name="Test Author", works_count=20, cited_by_count=200)
    
    @pytest.fixture
    def sample_papers(self):
        return [
            PaperData(paper_id=f"W{i}", title=f"Paper {i}", year=2020+i, authors=[], topic_label=f"Topic {i%3}")
            for i in range(10)
        ]
    
    def test_fetch_author_papers(self, use_case, sample_author, sample_papers):
        use_case.api_provider.get_author_papers_as_paper_data.return_value = sample_papers
        
        papers = use_case._fetch_author_papers(sample_author, max_papers=None)
        
        assert len(papers) == 10
        use_case.api_provider.get_author_papers_as_paper_data.assert_called_once()
    
    def test_fetch_author_papers_with_limit(self, use_case, sample_author, sample_papers):
        use_case.api_provider.get_author_papers_as_paper_data.return_value = sample_papers[:5]
        
        papers = use_case._fetch_author_papers(sample_author, max_papers=5)
        
        assert len(papers) == 5
    
    def test_create_temp_library(self, use_case, sample_author, sample_papers, temp_dir):
        temp_lib_path = temp_dir / "temp_lib"
        use_case.temp_library_manager.create_temp_library.return_value = temp_lib_path
        
        lib_path = use_case._create_temp_library(sample_author, sample_papers)
        
        assert lib_path == temp_lib_path
        use_case.temp_library_manager.create_temp_library.assert_called_once()
        use_case.library_manager.create_library_structure.assert_called_once()
    
    def test_create_permanent_library(self, use_case, sample_author, sample_papers, temp_dir):
        library_path = temp_dir / "perm_lib"
        
        lib_path = use_case._create_permanent_library(sample_author, sample_papers, library_path)
        
        assert lib_path == library_path
        use_case.library_manager.create_library_structure.assert_called_once()
    
