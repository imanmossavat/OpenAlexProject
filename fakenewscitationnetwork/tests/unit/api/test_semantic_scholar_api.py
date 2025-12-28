import pytest
from unittest.mock import Mock, patch
from ArticleCrawler.api.semantic_scholar_api import SemanticScholarAPIProvider


@pytest.mark.unit
class TestSemanticScholarAPI:
    
    @pytest.fixture
    def s2_provider(self, mock_logger):
        return SemanticScholarAPIProvider(wait=150, retries=2, logger=mock_logger)
    
    def test_initialization(self, s2_provider):
        assert s2_provider.wait == 150
        assert s2_provider.retries == 2
        assert s2_provider.failed_paper_ids == []
    
    @patch('ArticleCrawler.api.semantic_scholar_api.s2.api.get_paper')
    def test_get_paper_success(self, mock_get_paper, s2_provider):
        mock_paper = Mock()
        mock_paper.paperId = 'test123'
        mock_get_paper.return_value = mock_paper
        
        paper = s2_provider.get_paper('test123')
        assert paper is not None
        assert paper.paperId == 'test123'
    
    @patch('ArticleCrawler.api.semantic_scholar_api.s2.api.get_paper')
    def test_get_paper_failure_tracks_failed_id(self, mock_get_paper, s2_provider):
        mock_get_paper.side_effect = Exception("API Error")
        
        paper = s2_provider.get_paper('failed_id')
        assert paper is None
        assert 'failed_id' in s2_provider.failed_paper_ids
    
    @patch('ArticleCrawler.api.semantic_scholar_api.s2.api.get_paper')
    def test_get_paper_id_mismatch_tracked(self, mock_get_paper, s2_provider):
        mock_paper = Mock()
        mock_paper.paperId = 'different_id'
        mock_get_paper.return_value = mock_paper
        
        paper = s2_provider.get_paper('requested_id')
        assert ('requested_id', 'different_id') in s2_provider.inconsistent_api_response_paper_ids
    
    def test_get_papers_batch(self, s2_provider):
        with patch.object(s2_provider, 'get_paper', return_value=Mock()) as mock_get_paper:
            paper_ids = ['id1', 'id2', 'id3']
            s2_provider.get_papers(paper_ids)
            assert mock_get_paper.call_count == 3
    
    @patch('ArticleCrawler.api.semantic_scholar_api.s2.api.get_author')
    def test_get_author_papers_success(self, mock_get_author, s2_provider):
        mock_author = Mock()
        mock_paper1 = Mock()
        mock_paper1.paperId = 'paper1'
        mock_paper2 = Mock()
        mock_paper2.paperId = 'paper2'
        mock_author.papers = [mock_paper1, mock_paper2]
        mock_get_author.return_value = mock_author
        
        papers, paper_ids, total = s2_provider.get_author_papers('author123')
        assert len(papers) == 2
        assert len(paper_ids) == 2
        assert 'paper1' in paper_ids
        assert total == 2
    
    @patch('ArticleCrawler.api.semantic_scholar_api.s2.api.get_author')
    def test_get_author_papers_failure(self, mock_get_author, s2_provider):
        mock_get_author.side_effect = Exception("Author not found")
        
        papers, paper_ids, total = s2_provider.get_author_papers('invalid_author')
        assert papers == []
        assert paper_ids == []
        assert total is None
    
    def test_get_failed_and_inconsistent_papers(self, s2_provider):
        s2_provider._failed_paper_ids = ['failed1', 'failed2']
        s2_provider._inconsistent_api_response_paper_ids = [('req1', 'ret1')]
        
        result = s2_provider.get_failed_and_inconsistent_papers()
        assert result['failed'] == ['failed1', 'failed2']
        assert result['inconsistent'] == [('req1', 'ret1')]
