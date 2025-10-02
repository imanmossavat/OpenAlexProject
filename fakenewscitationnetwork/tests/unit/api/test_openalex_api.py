import pytest
from unittest.mock import Mock, patch, MagicMock
from ArticleCrawler.api.openalex_api import OpenAlexAPIProvider


@pytest.mark.unit
class TestOpenAlexAPI:
    
    @pytest.fixture
    def openalex_provider(self, mock_logger, monkeypatch):
        monkeypatch.setenv('OPENALEX_EMAIL', 'test@example.com')
        return OpenAlexAPIProvider(retries=1, logger=mock_logger)
    
    def test_initialization_without_email_raises_error(self, mock_logger, monkeypatch):
        monkeypatch.delenv('OPENALEX_EMAIL', raising=False)
        
        with patch('ArticleCrawler.api.openalex_api.os.getenv', return_value=None):
            with pytest.raises(ValueError, match="OPENALEX_EMAIL must be set"):
                OpenAlexAPIProvider(logger=mock_logger)
    
    def test_normalize_paper_id_with_w_prefix(self, openalex_provider):
        result = openalex_provider._normalize_paper_id('W2134567890')
        assert result == 'https://openalex.org/W2134567890'
    
    def test_normalize_paper_id_without_prefix(self, openalex_provider):
        result = openalex_provider._normalize_paper_id('2134567890')
        assert result == 'https://openalex.org/W2134567890'
    
    def test_normalize_paper_id_with_full_url(self, openalex_provider):
        full_url = 'https://openalex.org/W2134567890'
        result = openalex_provider._normalize_paper_id(full_url)
        assert result == full_url
    
    def test_normalize_author_id(self, openalex_provider):
        result = openalex_provider._normalize_author_id('A1234567890')
        assert result == 'https://openalex.org/A1234567890'
    
    def test_clean_id_from_url(self, openalex_provider):
        result = openalex_provider._clean_id('https://openalex.org/W2134567890')
        assert result == 'W2134567890'
    
    def test_clean_doi(self, openalex_provider):
        result = openalex_provider._clean_doi('https://doi.org/10.1234/test')
        assert result == '10.1234/test'
    
    def test_reconstruct_abstract_from_inverted_index(self, openalex_provider):
        inverted_index = {
            'This': [0],
            'is': [1],
            'a': [2],
            'test': [3]
        }
        result = openalex_provider._reconstruct_abstract_from_inverted_index(inverted_index)
        assert result == 'This is a test'
    
    def test_reconstruct_abstract_with_none_returns_none(self, openalex_provider):
        result = openalex_provider._reconstruct_abstract_from_inverted_index(None)
        assert result is None
    
    @patch('ArticleCrawler.api.openalex_api.Works')
    def test_get_paper_success(self, mock_works, openalex_provider, mock_openalex_response):
        mock_works_instance = MagicMock()
        mock_works_instance.__getitem__.return_value = mock_openalex_response
        mock_works.return_value = mock_works_instance
        
        paper = openalex_provider.get_paper('W2134567890')
        assert paper is not None
        assert hasattr(paper, 'paperId')
    
    @patch('ArticleCrawler.api.openalex_api.Works')
    def test_get_paper_failure_tracks_failed_id(self, mock_works, openalex_provider):
        mock_works_instance = MagicMock()
        mock_works_instance.__getitem__.side_effect = Exception("API Error")
        mock_works.return_value = mock_works_instance
        
        paper = openalex_provider.get_paper('W9999999999')
        assert paper is None
        assert 'W9999999999' in openalex_provider.failed_paper_ids
    
    def test_get_papers_calls_get_paper_for_each_id(self, openalex_provider):
        with patch.object(openalex_provider, 'get_paper', return_value=None) as mock_get_paper:
            paper_ids = ['W1', 'W2', 'W3']
            openalex_provider.get_papers(paper_ids)
            assert mock_get_paper.call_count == 3