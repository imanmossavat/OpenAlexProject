import pytest
from unittest.mock import Mock
from ArticleCrawler.library.author_search_service import AuthorSearchService
from ArticleCrawler.library.models import AuthorInfo, PaperData


class TestAuthorSearchService:
    
    @pytest.fixture
    def mock_api(self):
        api = Mock()
        return api
    
    @pytest.fixture
    def service(self, mock_api, mock_logger):
        return AuthorSearchService(mock_api, mock_logger)
    
    def test_search_authors(self, service, mock_api):
        mock_api.search_authors.return_value = [
            AuthorInfo(id="A1", name="John Doe", works_count=50, cited_by_count=500),
            AuthorInfo(id="A2", name="Jane Smith", works_count=30, cited_by_count=300)
        ]
        
        results = service.search_authors("John Doe")
        
        assert len(results) == 2
        assert results[0].id == "A1"
        assert results[0].name == "John Doe"
        assert results[0].works_count == 50
        mock_api.search_authors.assert_called_once_with("John Doe", limit=10)
    
    def test_search_authors_no_results(self, service, mock_api):
        mock_api.search_authors.return_value = []
        
        results = service.search_authors("Unknown Author")
        
        assert len(results) == 0
    
    def test_get_author_by_id(self, service, mock_api):
        author = AuthorInfo(id="A123", name="Test Author", works_count=10, cited_by_count=100)
        mock_api.search_authors.return_value = [author]
        
        result = service.get_author_by_id("A123")
        
        assert result is not None
        assert result.id == "A123"
    
    def test_get_author_by_id_not_found(self, service, mock_api):
        mock_api.search_authors.return_value = []
        
        result = service.get_author_by_id("A999")
        
        assert result is None
    
    def test_select_best_match_by_works_count(self, service):
        authors = [
            AuthorInfo(id="A1", name="Author 1", works_count=50, cited_by_count=500),
            AuthorInfo(id="A2", name="Author 2", works_count=30, cited_by_count=300),
            AuthorInfo(id="A3", name="Author 3", works_count=70, cited_by_count=200)
        ]
        
        best = service.select_best_match(authors, criteria="works_count")
        assert best.id == "A3"
    
    def test_select_best_match_by_citations(self, service):
        authors = [
            AuthorInfo(id="A1", name="Author 1", works_count=50, cited_by_count=500),
            AuthorInfo(id="A2", name="Author 2", works_count=30, cited_by_count=300),
            AuthorInfo(id="A3", name="Author 3", works_count=70, cited_by_count=200)
        ]
        
        best = service.select_best_match(authors, criteria="cited_by_count")
        assert best.id == "A1"
    
    def test_select_best_match_empty_list(self, service):
        result = service.select_best_match([], criteria="works_count")
        assert result is None