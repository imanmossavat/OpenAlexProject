import pytest
from unittest.mock import Mock, patch
from ArticleCrawler.pdf_processing.api_matcher import APIMetadataMatcher
from ArticleCrawler.pdf_processing.models import PDFMetadata, APIMatchResult


@pytest.mark.unit
class TestAPIMetadataMatcher:
    
    @pytest.fixture
    def mock_api_provider(self):
        return Mock()
    
    @pytest.fixture
    def matcher(self, mock_api_provider, mock_logger):
        return APIMetadataMatcher(mock_api_provider, logger=mock_logger)
    
    @pytest.fixture
    def sample_metadata_with_doi(self):
        return PDFMetadata(
            filename="test.pdf",
            title="Test Paper",
            doi="10.1234/test.2024.001",
            authors="John Doe",
            venue="Test Journal",
            year="2024"
        )
    
    @pytest.fixture
    def sample_metadata_no_doi(self):
        return PDFMetadata(
            filename="test2.pdf",
            title="Another Test Paper",
            authors="Jane Smith",
            venue="Test Conference",
            year="2023"
        )
    
    def test_initialization(self, mock_api_provider, mock_logger):
        matcher = APIMetadataMatcher(mock_api_provider, logger=mock_logger)
        assert matcher.api_provider == mock_api_provider
        assert matcher.logger == mock_logger
        assert matcher.request_delay == 0.5
        assert matcher.max_retries == 3
    
    def test_match_metadata_empty_list(self, matcher):
        results = matcher.match_metadata([])
        assert results == []
    
    @patch('time.sleep')
    def test_match_metadata_multiple_papers(self, mock_sleep, matcher, sample_metadata_with_doi, sample_metadata_no_doi):
        with patch.object(matcher, '_match_single') as mock_match:
            mock_match.side_effect = [
                APIMatchResult(metadata=sample_metadata_with_doi, matched=True, paper_id="W123"),
                APIMatchResult(metadata=sample_metadata_no_doi, matched=False)
            ]
            results = matcher.match_metadata([sample_metadata_with_doi, sample_metadata_no_doi])
            assert len(results) == 2
            assert results[0].matched is True
            assert results[1].matched is False
            assert mock_sleep.call_count == 1
    
    @patch('pyalex.Works')
    def test_match_by_doi_success(self, mock_works_class, matcher, sample_metadata_with_doi):
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.filter.return_value = mock_works_instance
        mock_works_instance.get.return_value = [{'id': 'https://openalex.org/W123456789', 'title': 'Test'}]
        result = matcher._match_by_doi(sample_metadata_with_doi)
        assert result.matched is True
        assert result.paper_id == "W123456789"
        assert result.match_method == "DOI"
        assert result.confidence == 1.0
    
    @patch('pyalex.Works')
    def test_match_by_doi_not_found(self, mock_works_class, matcher, sample_metadata_with_doi):
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.filter.return_value = mock_works_instance
        mock_works_instance.get.return_value = []
        result = matcher._match_by_doi(sample_metadata_with_doi)
        assert result.matched is False
    
    @patch('pyalex.Works')
    @patch('time.sleep')
    def test_match_by_doi_rate_limited(self, mock_sleep, mock_works_class, matcher, sample_metadata_with_doi, mock_logger):
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.filter.return_value = mock_works_instance
        mock_works_instance.get.side_effect = [
            Exception("429 Too Many Requests"),
            Exception("429 Too Many Requests"),
            [{'id': 'https://openalex.org/W123', 'title': 'Test'}]
        ]
        result = matcher._match_by_doi(sample_metadata_with_doi)
        assert result.matched is True
        assert mock_sleep.call_count == 2
        mock_logger.warning.assert_called()
    
    @patch('pyalex.Works')
    def test_match_by_title_success(self, mock_works_class, matcher, sample_metadata_no_doi):
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.search.return_value = mock_works_instance
        mock_works_instance.get.return_value = [
            {'id': 'https://openalex.org/W999', 'title': 'another test paper'},
            {'id': 'https://openalex.org/W888', 'title': 'different paper'}
        ]
        result = matcher._match_by_title(sample_metadata_no_doi)
        assert result.matched is True
        assert result.match_method == "Title"
        assert result.confidence > 0.8
    
    @patch('pyalex.Works')
    def test_match_by_title_no_results(self, mock_works_class, matcher, sample_metadata_no_doi):
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.search.return_value = mock_works_instance
        mock_works_instance.get.return_value = []
        result = matcher._match_by_title(sample_metadata_no_doi)
        assert result.matched is False
    
    def test_extract_paper_id_openalex(self, matcher):
        work = {'id': 'https://openalex.org/W123456789'}
        paper_id = matcher._extract_paper_id(work)
        assert paper_id == "W123456789"
    
    def test_extract_paper_id_no_id(self, matcher):
        work = {}
        paper_id = matcher._extract_paper_id(work)
        assert paper_id == ""