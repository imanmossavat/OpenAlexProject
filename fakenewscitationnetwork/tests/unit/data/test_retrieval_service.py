import pytest
from ArticleCrawler.data.retrieval_service import PaperRetrievalService


@pytest.mark.unit
class TestPaperRetrievalService:
    
    @pytest.fixture
    def retrieval_service(self, mock_api_provider, mock_logger):
        return PaperRetrievalService(mock_api_provider, mock_logger)
    
    def test_retrieve_papers_returns_empty_list_for_empty_input(self, retrieval_service):
        result = retrieval_service.retrieve_papers([])
        assert result == []
    
    def test_retrieve_papers_calls_api_get_papers(self, retrieval_service, mock_api_provider):
        paper_ids = ['W1', 'W2', 'W3']
        retrieval_service.retrieve_papers(paper_ids)
        mock_api_provider.get_papers.assert_called_once_with(paper_ids)
    
    def test_retrieve_author_papers_calls_api(self, retrieval_service, mock_api_provider):
        author_id = 'A123'
        retrieval_service.retrieve_author_papers(author_id)
        mock_api_provider.get_author_papers.assert_called_once_with(author_id)
    
    def test_get_failed_papers_returns_failed_ids(self, retrieval_service, mock_api_provider):
        mock_api_provider.failed_paper_ids = ['W1', 'W2']
        result = retrieval_service.get_failed_papers()
        assert result == ['W1', 'W2']
    
    def test_get_inconsistent_papers_returns_inconsistent_ids(self, retrieval_service, mock_api_provider):
        mock_api_provider.inconsistent_api_response_paper_ids = [('W1', 'W2')]
        result = retrieval_service.get_inconsistent_papers()
        assert result == [('W1', 'W2')]
    
    def test_get_retrieval_statistics(self, retrieval_service, mock_api_provider):
        mock_api_provider.get_failed_and_inconsistent_papers.return_value = {
            'failed': ['W1'],
            'inconsistent': []
        }
        result = retrieval_service.get_retrieval_statistics()
        assert 'failed' in result
        assert 'inconsistent' in result 
