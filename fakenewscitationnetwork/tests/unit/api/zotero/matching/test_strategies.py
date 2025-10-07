

import pytest
from unittest.mock import Mock, patch
from ArticleCrawler.api.zotero.matching.strategies import (
    TitleSimilarityCalculator,
    OpenAlexTitleMatchStrategy,
    SemanticScholarTitleMatchStrategy
)


@pytest.mark.unit
class TestTitleSimilarityCalculator:
    
    @pytest.fixture
    def calculator(self):
        return TitleSimilarityCalculator()
    
    def test_calculate_identical_titles(self, calculator):
        """Test similarity for identical titles."""
        title1 = "Machine Learning for Natural Language Processing"
        title2 = "Machine Learning for Natural Language Processing"
        
        similarity = calculator.calculate(title1, title2)
        
        assert similarity == 1.0
    
    def test_calculate_similar_titles(self, calculator):
        """Test similarity for similar titles."""
        title1 = "Machine Learning for NLP"
        title2 = "Machine Learning for Natural Language Processing"
        
        similarity = calculator.calculate(title1, title2)
        
        assert 0.5 < similarity < 1.0
    
    def test_calculate_different_titles(self, calculator):
        """Test similarity for completely different titles."""
        title1 = "Machine Learning Applications"
        title2 = "Quantum Computing Fundamentals"
        
        similarity = calculator.calculate(title1, title2)
        
        assert similarity < 0.5
    
    def test_calculate_case_insensitive(self, calculator):
        """Test that calculation is case-insensitive."""
        title1 = "MACHINE LEARNING"
        title2 = "machine learning"
        
        similarity = calculator.calculate(title1, title2)
        
        assert similarity == 1.0
    
    def test_calculate_ignores_punctuation(self, calculator):
        """Test that calculation ignores punctuation."""
        title1 = "Machine Learning: A Review"
        title2 = "Machine Learning A Review"
        
        similarity = calculator.calculate(title1, title2)
        
        assert similarity > 0.95
    
    def test_calculate_empty_titles(self, calculator):
        """Test similarity with empty titles."""
        assert calculator.calculate("", "") == 0.0
        assert calculator.calculate("Title", "") == 0.0
        assert calculator.calculate("", "Title") == 0.0
        assert calculator.calculate(None, "Title") == 0.0
        assert calculator.calculate("Title", None) == 0.0
    
    def test_normalize_removes_extra_spaces(self, calculator):
        """Test normalization removes extra spaces."""
        normalized = calculator._normalize("Title  with   spaces")
        
        assert "  " not in normalized
        assert normalized == "title with spaces"
    
    def test_normalize_handles_special_characters(self, calculator):
        """Test normalization handles special characters."""
        normalized = calculator._normalize("Title: A Review (2024) - Updated!")
        
        assert ':' not in normalized
        assert '(' not in normalized
        assert ')' not in normalized
        assert '-' not in normalized
        assert '!' not in normalized


@pytest.mark.unit
class TestOpenAlexTitleMatchStrategy:
    
    @pytest.fixture
    def strategy(self):
        return OpenAlexTitleMatchStrategy()
    
    @patch('pyalex.Works')
    def test_search_success(self, mock_works_class, strategy):
        """Test successful search with results."""
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.search.return_value = mock_works_instance
        
        mock_results = [
            {
                'id': 'https://openalex.org/W123456',
                'title': 'Test Paper Title',
                'publication_year': 2024,
                'primary_location': {
                    'source': {'display_name': 'Test Journal'}
                },
                'doi': 'https://doi.org/10.1234/test'
            },
            {
                'id': 'https://openalex.org/W789012',
                'title': 'Another Paper',
                'publication_year': 2023,
                'primary_location': None,
                'doi': None
            }
        ]
        mock_works_instance.get.return_value = mock_results
        
        strategy.min_delay = 0
        results = strategy.search("test query")
        
        assert len(results) == 2
        assert results[0]['paper_id'] == 'W123456'
        assert results[0]['title'] == 'Test Paper Title'
        assert results[0]['year'] == 2024
        assert results[0]['venue'] == 'Test Journal'
        assert results[0]['doi'] == '10.1234/test'
        
        assert results[1]['paper_id'] == 'W789012'
        assert results[1]['venue'] is None
        assert results[1]['doi'] is None
    
    @patch('pyalex.Works')
    def test_search_no_results(self, mock_works_class, strategy):
        """Test search with no results."""
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.search.return_value = mock_works_instance
        mock_works_instance.get.return_value = []
        
        strategy.min_delay = 0
        results = strategy.search("nonexistent paper")
        
        assert results == []
    
    @patch('pyalex.Works')
    def test_search_filters_no_title(self, mock_works_class, strategy):
        """Test search filters out results without titles."""
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.search.return_value = mock_works_instance
        
        mock_results = [
            {
                'id': 'https://openalex.org/W123456',
                'title': 'Valid Paper',
                'publication_year': 2024
            },
            {
                'id': 'https://openalex.org/W789012',
                'title': '', 
                'publication_year': 2023
            },
            {
                'id': 'https://openalex.org/W345678',
                'publication_year': 2022
            }
        ]
        mock_works_instance.get.return_value = mock_results
        
        strategy.min_delay = 0
        results = strategy.search("test query")
        
        assert len(results) == 1
        assert results[0]['title'] == 'Valid Paper'
    
    @patch('pyalex.Works')
    def test_search_max_results_limit(self, mock_works_class, strategy):
        """Test that search respects max_results parameter."""
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.search.return_value = mock_works_instance
        
        mock_results = [
            {'id': f'https://openalex.org/W{i}', 'title': f'Paper {i}', 'publication_year': 2024}
            for i in range(20)
        ]
        mock_works_instance.get.return_value = mock_results
        
        strategy.min_delay = 0
        results = strategy.search("test query", max_results=5)
        
        assert len(results) == 5
    
    def test_extract_venue_from_primary_location(self, strategy):
        """Test venue extraction from primary_location."""
        result = {
            'primary_location': {
                'source': {'display_name': 'Nature'}
            }
        }
        
        venue = strategy._extract_venue(result)
        
        assert venue == 'Nature'
    
    def test_extract_venue_from_host_venue(self, strategy):
        """Test venue extraction from host_venue."""
        result = {
            'primary_location': None,
            'host_venue': {'display_name': 'Science'}
        }
        
        venue = strategy._extract_venue(result)
        
        assert venue == 'Science'
    
    def test_extract_venue_none(self, strategy):
        """Test venue extraction returns None when not found."""
        result = {
            'primary_location': None,
            'host_venue': None
        }
        
        venue = strategy._extract_venue(result)
        
        assert venue is None
    
    def test_rate_limit_enforced(self, strategy):
        """Test that rate limiting is enforced."""
        import time
        
        strategy.min_delay = 0.1
        
        start = time.time()
        strategy._rate_limit()
        strategy._rate_limit()
        elapsed = time.time() - start
        
        assert elapsed >= 0.1


@pytest.mark.unit
class TestSemanticScholarTitleMatchStrategy:
    
    @pytest.fixture
    def strategy(self):
        return SemanticScholarTitleMatchStrategy()
    
    @patch('requests.get')
    def test_search_success(self, mock_get, strategy):
        """Test successful search with results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'paperId': 'abc123',
                    'title': 'Test Paper',
                    'year': 2024,
                    'venue': {'name': 'Test Conference'}
                },
                {
                    'paperId': 'def456',
                    'title': 'Another Paper',
                    'year': 2023,
                    'venue': 'Test Journal'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        strategy.min_delay = 0
        results = strategy.search("test query")
        
        assert len(results) == 2
        assert results[0]['paper_id'] == 'abc123'
        assert results[0]['title'] == 'Test Paper'
        assert results[0]['year'] == 2024
        assert results[0]['venue'] == 'Test Conference'
        assert results[0]['doi'] is None
        
        assert results[1]['paper_id'] == 'def456'
        assert results[1]['venue'] == 'Test Journal'
    
    @patch('requests.get')
    def test_search_no_results(self, mock_get, strategy):
        """Test search with no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response
        
        strategy.min_delay = 0
        results = strategy.search("nonexistent paper")
        
        assert results == []
    
    @patch('requests.get')
    def test_search_filters_no_title(self, mock_get, strategy):
        """Test search filters out results without titles."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [
                {'paperId': 'abc123', 'title': 'Valid Paper', 'year': 2024},
                {'paperId': 'def456', 'title': '', 'year': 2023},
                {'paperId': 'ghi789', 'year': 2022}
            ]
        }
        mock_get.return_value = mock_response
        
        strategy.min_delay = 0
        results = strategy.search("test query")
        
        assert len(results) == 1
        assert results[0]['title'] == 'Valid Paper'
    
    @patch('requests.get')
    def test_search_api_error(self, mock_get, strategy):
        """Test search handles API errors."""
        mock_get.side_effect = Exception("API Error")
        
        strategy.min_delay = 0
        
        with pytest.raises(Exception, match="API Error"):
            strategy.search("test query")
    
    @patch('requests.get')
    def test_search_calls_api_correctly(self, mock_get, strategy):
        """Test that search calls API with correct parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response
        
        strategy.min_delay = 0
        strategy.search("test query", max_results=15)
        
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        
        assert 'https://api.semanticscholar.org/graph/v1/paper/search' in args[0]
        assert kwargs['params']['query'] == 'test query'
        assert kwargs['params']['limit'] == 15
        assert 'paperId' in kwargs['params']['fields']
    
    def test_rate_limit_enforced(self, strategy):
        """Test that rate limiting is enforced."""
        import time
        
        strategy.min_delay = 0.1
        
        start = time.time()
        strategy._rate_limit()
        strategy._rate_limit()
        elapsed = time.time() - start
        
        assert elapsed >= 0.1