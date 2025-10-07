

import pytest
from unittest.mock import Mock, patch
from ArticleCrawler.api.zotero.matching.matcher import (
    ZoteroMatcher,
    MatchResult,
    MatchCandidate
)


@pytest.mark.unit
class TestMatchCandidate:
    
    def test_match_candidate_creation(self):
        """Test MatchCandidate dataclass creation."""
        candidate = MatchCandidate(
            paper_id='W123456',
            title='Test Paper',
            similarity=0.95,
            year=2024,
            venue='Test Journal',
            doi='10.1234/test'
        )
        
        assert candidate.paper_id == 'W123456'
        assert candidate.title == 'Test Paper'
        assert candidate.similarity == 0.95
        assert candidate.year == 2024
        assert candidate.venue == 'Test Journal'
        assert candidate.doi == '10.1234/test'
    
    def test_match_candidate_optional_fields(self):
        """Test MatchCandidate with optional fields as None."""
        candidate = MatchCandidate(
            paper_id='W123456',
            title='Test Paper',
            similarity=0.85
        )
        
        assert candidate.year is None
        assert candidate.venue is None
        assert candidate.doi is None


@pytest.mark.unit
class TestMatchResult:
    
    def test_match_result_matched(self):
        """Test MatchResult for successful match."""
        result = MatchResult(
            zotero_key='ZKEY123',
            title='Test Paper',
            matched=True,
            paper_id='W123456',
            confidence=0.95,
            match_method='doi'
        )
        
        assert result.matched is True
        assert result.paper_id == 'W123456'
        assert result.confidence == 0.95
        assert result.match_method == 'doi'
        assert result.error is None
        assert result.candidates == []
    
    def test_match_result_unmatched_with_candidates(self):
        """Test MatchResult for unmatched with candidates."""
        candidates = [
            MatchCandidate(paper_id='W111', title='Paper 1', similarity=0.75),
            MatchCandidate(paper_id='W222', title='Paper 2', similarity=0.70)
        ]
        
        result = MatchResult(
            zotero_key='ZKEY123',
            title='Test Paper',
            matched=False,
            confidence=0.75,
            error='No auto-match found',
            candidates=candidates
        )
        
        assert result.matched is False
        assert result.paper_id is None
        assert len(result.candidates) == 2
        assert result.error == 'No auto-match found'


@pytest.mark.unit
class TestZoteroMatcher:
    
    @pytest.fixture
    def mock_api_provider(self):
        """Mock API provider."""
        api = Mock()
        api.__class__.__name__ = 'OpenAlexProvider'
        return api
    
    @pytest.fixture
    def mock_title_strategy(self):
        """Mock title matching strategy."""
        return Mock()
    
    @pytest.fixture
    def mock_similarity_calculator(self, monkeypatch):
        """Mock similarity calculator."""
        mock_calc = Mock()
        monkeypatch.setattr(
            'ArticleCrawler.api.zotero.matching.matcher.TitleSimilarityCalculator',
            Mock(return_value=mock_calc)
        )
        return mock_calc
    
    def test_init_with_openalex_provider(self, mock_api_provider, mock_logger):
        """Test initialization detects OpenAlex provider."""
        matcher = ZoteroMatcher(mock_api_provider, logger=mock_logger)
        
        assert matcher.api == mock_api_provider
        assert matcher._detect_api_type() == 'openalex'
    
    def test_init_with_semantic_scholar_provider(self, mock_logger):
        """Test initialization detects Semantic Scholar provider."""
        api = Mock()
        api.__class__.__name__ = 'SemanticScholarProvider'
        
        matcher = ZoteroMatcher(api, logger=mock_logger)
        
        assert matcher._detect_api_type() == 'semantic_scholar'
    
    def test_init_with_custom_strategy(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test initialization with custom title strategy."""
        matcher = ZoteroMatcher(
            mock_api_provider,
            title_strategy=mock_title_strategy,
            logger=mock_logger
        )
        
        assert matcher.title_strategy == mock_title_strategy
    
    def test_init_unknown_api_type_raises_error(self, mock_logger):
        """Test initialization with unknown API type raises error."""
        api = Mock()
        api.__class__.__name__ = 'UnknownProvider'
        
        with pytest.raises(ValueError, match="No title strategy available"):
            ZoteroMatcher(api, logger=mock_logger)
    
    def test_detect_api_type_openalex(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test API type detection for OpenAlex."""
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        
        assert matcher._detect_api_type() == 'openalex'
    
    def test_detect_api_type_semantic_scholar(self, mock_title_strategy, mock_logger):
        """Test API type detection for Semantic Scholar."""
        api = Mock()
        api.__class__.__name__ = 'S2Provider'
        
        matcher = ZoteroMatcher(api, title_strategy=mock_title_strategy, logger=mock_logger)
        
        assert matcher._detect_api_type() == 'semantic_scholar'
    
    def test_match_items_all_successful(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test matching multiple items all successfully."""
        mock_title_strategy.search.return_value = [
            {'paper_id': 'W123', 'title': 'Paper 1', 'year': 2024, 'venue': None, 'doi': None}
        ]
        
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        matcher.similarity_calculator.calculate.return_value = 0.90
        
        items = [
            {'zotero_key': 'Z1', 'title': 'Paper 1', 'doi': ''},
            {'zotero_key': 'Z2', 'title': 'Paper 2', 'doi': ''}
        ]
        
        results = matcher.match_items(items)
        
        assert len(results) == 2
        assert all(r.matched for r in results)
    
    def test_match_items_some_failed(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test matching with some failures."""
        def search_side_effect(title, max_results=10):
            if 'Paper 1' in title:
                return [{'paper_id': 'W123', 'title': 'Paper 1', 'year': 2024, 'venue': None, 'doi': None}]
            return []
        
        mock_title_strategy.search.side_effect = search_side_effect
        
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        matcher.similarity_calculator.calculate.return_value = 0.90
        
        items = [
            {'zotero_key': 'Z1', 'title': 'Paper 1', 'doi': ''},
            {'zotero_key': 'Z2', 'title': 'Nonexistent Paper', 'doi': ''}
        ]
        
        results = matcher.match_items(items)
        
        assert len(results) == 2
        assert results[0].matched is True
        assert results[1].matched is False
    
    @patch('pyalex.Works')
    def test_match_by_doi_openalex_success(self, mock_works_class, mock_api_provider, mock_title_strategy, mock_logger):
        """Test DOI matching with OpenAlex succeeds."""
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.filter.return_value = mock_works_instance
        mock_works_instance.get.return_value = [
            {'id': 'https://openalex.org/W123456', 'title': 'Test Paper'}
        ]
        
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        
        metadata = {
            'zotero_key': 'ZKEY123',
            'title': 'Test Paper',
            'doi': '10.1234/test'
        }
        
        result = matcher._match_by_doi(metadata)
        
        assert result.matched is True
        assert result.paper_id == 'W123456'
        assert result.confidence == 1.0
        assert result.match_method == 'doi'
    
    @patch('pyalex.Works')
    def test_match_by_doi_openalex_not_found(self, mock_works_class, mock_api_provider, mock_title_strategy, mock_logger):
        """Test DOI matching with OpenAlex when DOI not found."""
        mock_works_instance = Mock()
        mock_works_class.return_value = mock_works_instance
        mock_works_instance.filter.return_value = mock_works_instance
        mock_works_instance.get.return_value = []
        
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        
        metadata = {
            'zotero_key': 'ZKEY123',
            'title': 'Test Paper',
            'doi': '10.1234/nonexistent'
        }
        
        result = matcher._match_by_doi(metadata)
        
        assert result.matched is False
        assert 'DOI not found' in result.error
    
    @patch('requests.get')
    def test_match_by_doi_semantic_scholar_success(self, mock_get, mock_title_strategy, mock_logger):
        """Test DOI matching with Semantic Scholar succeeds."""
        api = Mock()
        api.__class__.__name__ = 'SemanticScholarProvider'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'paperId': 'abc123',
            'title': 'Test Paper'
        }
        mock_get.return_value = mock_response
        
        matcher = ZoteroMatcher(api, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        
        metadata = {
            'zotero_key': 'ZKEY123',
            'title': 'Test Paper',
            'doi': '10.1234/test'
        }
        
        result = matcher._match_by_doi(metadata)
        
        assert result.matched is True
        assert result.paper_id == 'abc123'
        assert result.confidence == 1.0
        assert result.match_method == 'doi'
    
    def test_match_by_title_high_similarity_auto_match(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test title matching with high similarity auto-matches."""
        mock_title_strategy.search.return_value = [
            {
                'paper_id': 'W123456',
                'title': 'Test Paper Title',
                'year': 2024,
                'venue': 'Test Journal',
                'doi': '10.1234/test'
            }
        ]
        
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        matcher.similarity_calculator = Mock()
        matcher.similarity_calculator.calculate.return_value = 0.90
        
        metadata = {
            'zotero_key': 'ZKEY123',
            'title': 'Test Paper Title'
        }
        
        result = matcher._match_by_title(metadata)
        
        assert result.matched is True
        assert result.paper_id == 'W123456'
        assert result.confidence == 0.90
        assert result.match_method == 'title_search'
    
    def test_match_by_title_medium_similarity_candidates(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test title matching with medium similarity returns candidates."""
        mock_title_strategy.search.return_value = [
            {'paper_id': 'W111', 'title': 'Similar Paper 1', 'year': 2024, 'venue': None, 'doi': None},
            {'paper_id': 'W222', 'title': 'Similar Paper 2', 'year': 2023, 'venue': None, 'doi': None}
        ]
        
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        matcher.similarity_calculator = Mock()
        matcher.similarity_calculator.calculate.side_effect = [0.75, 0.70]
        
        metadata = {
            'zotero_key': 'ZKEY123',
            'title': 'Test Paper'
        }
        
        result = matcher._match_by_title(metadata)
        
        assert result.matched is False
        assert len(result.candidates) == 2
        assert result.candidates[0].paper_id == 'W111'
        assert result.candidates[0].similarity == 0.75
        assert result.confidence == 0.75
    
    def test_match_by_title_low_similarity_no_candidates(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test title matching with low similarity returns no candidates."""
        mock_title_strategy.search.return_value = [
            {'paper_id': 'W111', 'title': 'Different Paper', 'year': 2024, 'venue': None, 'doi': None}
        ]
        
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        matcher.similarity_calculator = Mock()
        matcher.similarity_calculator.calculate.return_value = 0.50
        
        metadata = {
            'zotero_key': 'ZKEY123',
            'title': 'Test Paper'
        }
        
        result = matcher._match_by_title(metadata)
        
        assert result.matched is False
        assert len(result.candidates) == 0
    
    def test_match_by_title_no_search_results(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test title matching with no search results."""
        mock_title_strategy.search.return_value = []
        
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        
        metadata = {
            'zotero_key': 'ZKEY123',
            'title': 'Nonexistent Paper'
        }
        
        result = matcher._match_by_title(metadata)
        
        assert result.matched is False
        assert result.error == 'No results found'
    
    def test_match_by_title_search_error(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test title matching handles search errors."""
        mock_title_strategy.search.side_effect = Exception("API Error")
        
        matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
        matcher.min_delay = 0
        
        metadata = {
            'zotero_key': 'ZKEY123',
            'title': 'Test Paper'
        }
        
        result = matcher._match_by_title(metadata)
        
        assert result.matched is False
        assert 'Search error' in result.error
    
    def test_match_single_item_tries_doi_first(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test that match_single_item tries DOI before title."""
        with patch.object(ZoteroMatcher, '_match_by_doi') as mock_doi, \
             patch.object(ZoteroMatcher, '_match_by_title') as mock_title:
            
            mock_doi.return_value = MatchResult(
                zotero_key='ZKEY123',
                title='Test',
                matched=True,
                paper_id='W123'
            )
            
            matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
            matcher.min_delay = 0
            
            metadata = {
                'zotero_key': 'ZKEY123',
                'title': 'Test Paper',
                'doi': '10.1234/test'
            }
            
            result = matcher.match_single_item(metadata)
            
            mock_doi.assert_called_once()
            mock_title.assert_not_called()
            assert result.matched is True
    
    def test_match_single_item_falls_back_to_title(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test that match_single_item falls back to title if DOI fails."""
        with patch.object(ZoteroMatcher, '_match_by_doi') as mock_doi, \
             patch.object(ZoteroMatcher, '_match_by_title') as mock_title:
            
            mock_doi.return_value = MatchResult(
                zotero_key='ZKEY123',
                title='Test',
                matched=False
            )
            
            mock_title.return_value = MatchResult(
                zotero_key='ZKEY123',
                title='Test',
                matched=True,
                paper_id='W123'
            )
            
            matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
            matcher.min_delay = 0
            
            metadata = {
                'zotero_key': 'ZKEY123',
                'title': 'Test Paper',
                'doi': '10.1234/test'
            }
            
            result = matcher.match_single_item(metadata)
            
            mock_doi.assert_called_once()
            mock_title.assert_called_once()
            assert result.matched is True
    
    def test_match_single_item_no_doi_uses_title(self, mock_api_provider, mock_title_strategy, mock_logger):
        """Test that match_single_item uses title when no DOI."""
        with patch.object(ZoteroMatcher, '_match_by_doi') as mock_doi, \
             patch.object(ZoteroMatcher, '_match_by_title') as mock_title:
            
            mock_title.return_value = MatchResult(
                zotero_key='ZKEY123',
                title='Test',
                matched=True,
                paper_id='W123'
            )
            
            matcher = ZoteroMatcher(mock_api_provider, title_strategy=mock_title_strategy, logger=mock_logger)
            matcher.min_delay = 0
            
            metadata = {
                'zotero_key': 'ZKEY123',
                'title': 'Test Paper',
                'doi': ''
            }
            
            result = matcher.match_single_item(metadata)
            
            mock_doi.assert_not_called()
            mock_title.assert_called_once()