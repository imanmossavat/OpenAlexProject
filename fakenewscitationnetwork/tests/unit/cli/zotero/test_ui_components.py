

import pytest
from unittest.mock import Mock
from ArticleCrawler.cli.zotero.ui_components import (
    ZoteroCollectionSelector,
    SelectionModeChooser,
    PaperSelector,
    MatchReviewer,
    MatchResultsPresenter
)
from ArticleCrawler.api.zotero.matching.matcher import MatchResult, MatchCandidate


@pytest.mark.unit
class TestZoteroCollectionSelector:
    
    @pytest.fixture
    def mock_prompter(self):
        return Mock()
    
    @pytest.fixture
    def mock_console(self):
        return Mock()
    
    @pytest.fixture
    def selector(self, mock_prompter, mock_console):
        return ZoteroCollectionSelector(mock_prompter, mock_console)
    
    @pytest.fixture
    def sample_collections(self):
        return [
            {'key': 'COL1', 'name': 'Collection 1'},
            {'key': 'COL2', 'name': 'Collection 2'},
            {'key': 'COL3', 'name': 'Collection 3'}
        ]
    
    def test_select_valid_choice(self, selector, mock_prompter, sample_collections):
        """Test selecting a valid collection."""
        mock_prompter.input.return_value = '2'
        
        result = selector.select(sample_collections)
        
        assert result == sample_collections[1]
        assert result['name'] == 'Collection 2'
    
    def test_select_first_collection(self, selector, mock_prompter, sample_collections):
        """Test selecting the first collection."""
        mock_prompter.input.return_value = '1'
        
        result = selector.select(sample_collections)
        
        assert result == sample_collections[0]
    
    def test_select_last_collection(self, selector, mock_prompter, sample_collections):
        """Test selecting the last collection."""
        mock_prompter.input.return_value = '3'
        
        result = selector.select(sample_collections)
        
        assert result == sample_collections[2]
    
    def test_select_invalid_then_valid(self, selector, mock_prompter, sample_collections):
        """Test invalid choice followed by valid choice."""
        mock_prompter.input.side_effect = ['invalid', '2']
        
        result = selector.select(sample_collections)
        
        assert result == sample_collections[1]
        mock_prompter.error.assert_called_once()
    
    def test_select_out_of_range_then_valid(self, selector, mock_prompter, sample_collections):
        """Test out of range choice followed by valid choice."""
        mock_prompter.input.side_effect = ['5', '1']
        
        result = selector.select(sample_collections)
        
        assert result == sample_collections[0]
        mock_prompter.error.assert_called_once()
    
    def test_select_zero_then_valid(self, selector, mock_prompter, sample_collections):
        """Test zero choice followed by valid choice."""
        mock_prompter.input.side_effect = ['0', '1']
        
        result = selector.select(sample_collections)
        
        assert result == sample_collections[0]
        mock_prompter.error.assert_called_once()


@pytest.mark.unit
class TestSelectionModeChooser:
    
    @pytest.fixture
    def mock_prompter(self):
        return Mock()
    
    @pytest.fixture
    def mock_console(self):
        return Mock()
    
    @pytest.fixture
    def chooser(self, mock_prompter, mock_console):
        return SelectionModeChooser(mock_prompter, mock_console)
    
    def test_choose_all_mode(self, chooser, mock_prompter):
        """Test choosing 'all' mode."""
        mock_prompter.input.return_value = '1'
        
        result = chooser.choose()
        
        assert result == 'all'
    
    def test_choose_individual_mode(self, chooser, mock_prompter):
        """Test choosing 'individual' mode."""
        mock_prompter.input.return_value = '2'
        
        result = chooser.choose()
        
        assert result == 'individual'
    
    def test_choose_invalid_then_valid(self, chooser, mock_prompter):
        """Test invalid choice followed by valid choice."""
        mock_prompter.input.side_effect = ['3', '1']
        
        result = chooser.choose()
        
        assert result == 'all'
        mock_prompter.error.assert_called_once()


@pytest.mark.unit
class TestPaperSelector:
    
    @pytest.fixture
    def mock_prompter(self):
        return Mock()
    
    @pytest.fixture
    def mock_console(self):
        return Mock()
    
    @pytest.fixture
    def mock_formatter(self):
        formatter = Mock()
        formatter.format_collection_preview.return_value = "Formatted paper preview"
        return formatter
    
    @pytest.fixture
    def selector(self, mock_prompter, mock_console, mock_formatter):
        return PaperSelector(mock_prompter, mock_console, mock_formatter)
    
    @pytest.fixture
    def sample_items(self):
        return [
            {'zotero_key': 'Z1', 'title': 'Paper 1'},
            {'zotero_key': 'Z2', 'title': 'Paper 2'},
            {'zotero_key': 'Z3', 'title': 'Paper 3'},
            {'zotero_key': 'Z4', 'title': 'Paper 4'},
            {'zotero_key': 'Z5', 'title': 'Paper 5'}
        ]
    
    def test_select_single_paper(self, selector, mock_prompter, sample_items):
        """Test selecting a single paper."""
        mock_prompter.input.return_value = '2'
        
        result = selector.select(sample_items)
        
        assert len(result) == 1
        assert result[0] == sample_items[1]
    
    def test_select_multiple_papers(self, selector, mock_prompter, sample_items):
        """Test selecting multiple papers."""
        mock_prompter.input.return_value = '1 3 5'
        
        result = selector.select(sample_items)
        
        assert len(result) == 3
        assert result[0] == sample_items[0]
        assert result[1] == sample_items[2]
        assert result[2] == sample_items[4]
    
    def test_select_range(self, selector, mock_prompter, sample_items):
        """Test selecting a range of papers."""
        mock_prompter.input.return_value = '2-4'
        
        result = selector.select(sample_items)
        
        assert len(result) == 3
        assert result == sample_items[1:4]
    
    def test_select_mixed_format(self, selector, mock_prompter, sample_items):
        """Test selecting with mixed format (individual + range)."""
        mock_prompter.input.return_value = '1 3-4'
        
        result = selector.select(sample_items)
        
        assert len(result) == 3
        assert sample_items[0] in result
        assert sample_items[2] in result
        assert sample_items[3] in result
    
    def test_select_empty_cancels(self, selector, mock_prompter, sample_items):
        """Test empty input cancels selection."""
        mock_prompter.input.return_value = ''
        
        result = selector.select(sample_items)
        
        assert result == []
    
    def test_select_invalid_then_valid(self, selector, mock_prompter, sample_items):
        """Test invalid selection followed by valid selection."""
        mock_prompter.input.side_effect = ['invalid', '1']
        
        result = selector.select(sample_items)
        
        assert len(result) == 1
        assert result[0] == sample_items[0]
        mock_prompter.error.assert_called_once()
    
    def test_parse_selection_single(self, selector):
        """Test parsing single number."""
        indices = selector._parse_selection('3', 5)
        
        assert indices == [2]  # 0-indexed
    
    def test_parse_selection_multiple(self, selector):
        """Test parsing multiple numbers."""
        indices = selector._parse_selection('1 3 5', 5)
        
        assert indices == [0, 2, 4]
    
    def test_parse_selection_range(self, selector):
        """Test parsing range."""
        indices = selector._parse_selection('2-4', 5)
        
        assert indices == [1, 2, 3]
    
    def test_parse_selection_invalid_range(self, selector):
        """Test parsing invalid range raises error."""
        with pytest.raises(ValueError, match="Invalid range"):
            selector._parse_selection('4-2', 5)
    
    def test_parse_selection_invalid_format(self, selector):
        """Test parsing invalid format raises error."""
        with pytest.raises(ValueError):
            selector._parse_selection('1-2-3', 5)


@pytest.mark.unit
class TestMatchReviewer:
    
    @pytest.fixture
    def mock_prompter(self):
        return Mock()
    
    @pytest.fixture
    def mock_console(self):
        return Mock()
    
    @pytest.fixture
    def reviewer(self, mock_prompter, mock_console):
        return MatchReviewer(mock_prompter, mock_console)
    
    @pytest.fixture
    def match_result_with_candidates(self):
        candidates = [
            MatchCandidate(
                paper_id='W111',
                title='Very Similar Paper',
                similarity=0.90,
                year=2024,
                venue='Top Journal',
                doi='10.1234/test1'
            ),
            MatchCandidate(
                paper_id='W222',
                title='Somewhat Similar Paper',
                similarity=0.75,
                year=2023,
                venue='Good Conference',
                doi=None
            ),
            MatchCandidate(
                paper_id='W333',
                title='Less Similar Paper',
                similarity=0.65,
                year=2022,
                venue=None,
                doi=None
            )
        ]
        
        return MatchResult(
            zotero_key='ZKEY123',
            title='Original Paper Title',
            matched=False,
            candidates=candidates
        )
    
    def test_review_select_first_candidate(self, reviewer, mock_prompter, match_result_with_candidates):
        """Test selecting the first candidate."""
        mock_prompter.input.return_value = '1'
        
        result = reviewer.review(match_result_with_candidates)
        
        assert result == 'W111'
    
    def test_review_select_middle_candidate(self, reviewer, mock_prompter, match_result_with_candidates):
        """Test selecting a middle candidate."""
        mock_prompter.input.return_value = '2'
        
        result = reviewer.review(match_result_with_candidates)
        
        assert result == 'W222'
    
    def test_review_skip_selection(self, reviewer, mock_prompter, match_result_with_candidates):
        """Test skipping selection."""
        mock_prompter.input.return_value = ''
        
        result = reviewer.review(match_result_with_candidates)
        
        assert result is None
    
    def test_review_invalid_then_valid(self, reviewer, mock_prompter, match_result_with_candidates):
        """Test invalid selection followed by valid selection."""
        mock_prompter.input.side_effect = ['invalid', '1']
        
        result = reviewer.review(match_result_with_candidates)
        
        assert result == 'W111'
        mock_prompter.error.assert_called_once()
    
    def test_review_out_of_range_then_valid(self, reviewer, mock_prompter, match_result_with_candidates):
        """Test out of range selection followed by valid selection."""
        mock_prompter.input.side_effect = ['10', '2']
        
        result = reviewer.review(match_result_with_candidates)
        
        assert result == 'W222'
        mock_prompter.error.assert_called_once()


@pytest.mark.unit
class TestMatchResultsPresenter:
    
    @pytest.fixture
    def mock_console(self):
        return Mock()
    
    @pytest.fixture
    def presenter(self, mock_console):
        return MatchResultsPresenter(mock_console)
    
    @pytest.fixture
    def mock_reviewer(self):
        return Mock()
    
    def test_present_all_auto_matched(self, presenter, mock_reviewer):
        """Test presenting all auto-matched results."""
        results = [
            MatchResult(
                zotero_key='Z1',
                title='Paper 1',
                matched=True,
                paper_id='W111',
                confidence=0.95,
                match_method='doi'
            ),
            MatchResult(
                zotero_key='Z2',
                title='Paper 2',
                matched=True,
                paper_id='W222',
                confidence=0.90,
                match_method='title_search'
            )
        ]
        
        paper_ids = presenter.present(results, mock_reviewer)
        
        assert paper_ids == ['W111', 'W222']
        mock_reviewer.review.assert_not_called()
    
    def test_present_with_manual_review(self, presenter, mock_reviewer):
        """Test presenting with manual review needed."""
        auto_matched = MatchResult(
            zotero_key='Z1',
            title='Auto Matched Paper',
            matched=True,
            paper_id='W111'
        )
        
        needs_review = MatchResult(
            zotero_key='Z2',
            title='Manual Review Paper',
            matched=False,
            candidates=[
                MatchCandidate(paper_id='W222', title='Candidate', similarity=0.75)
            ]
        )
        
        mock_reviewer.review.return_value = 'W222'
        
        paper_ids = presenter.present([auto_matched, needs_review], mock_reviewer)
        
        assert paper_ids == ['W111', 'W222']
        mock_reviewer.review.assert_called_once_with(needs_review)
    
    def test_present_manual_review_skipped(self, presenter, mock_reviewer):
        """Test presenting when manual review is skipped."""
        needs_review = MatchResult(
            zotero_key='Z1',
            title='Manual Review Paper',
            matched=False,
            candidates=[
                MatchCandidate(paper_id='W111', title='Candidate', similarity=0.75)
            ]
        )
        
        mock_reviewer.review.return_value = None
        
        paper_ids = presenter.present([needs_review], mock_reviewer)
        
        assert paper_ids == []
    
    def test_present_with_failures(self, presenter, mock_reviewer):
        """Test presenting with failed matches."""
        auto_matched = MatchResult(
            zotero_key='Z1',
            title='Successful Paper',
            matched=True,
            paper_id='W111'
        )
        
        failed = MatchResult(
            zotero_key='Z2',
            title='Failed Paper',
            matched=False,
            error='No results found',
            candidates=[]
        )
        
        paper_ids = presenter.present([auto_matched, failed], mock_reviewer)
        
        assert paper_ids == ['W111']
        mock_reviewer.review.assert_not_called()
    
    def test_present_empty_results(self, presenter, mock_reviewer):
        """Test presenting empty results."""
        paper_ids = presenter.present([], mock_reviewer)
        
        assert paper_ids == []
    
    def test_present_mixed_results(self, presenter, mock_reviewer):
        """Test presenting mixed results (auto, manual, failed)."""
        results = [
            MatchResult(zotero_key='Z1', title='Auto', matched=True, paper_id='W111'),
            MatchResult(
                zotero_key='Z2',
                title='Manual',
                matched=False,
                candidates=[MatchCandidate(paper_id='W222', title='C', similarity=0.75)]
            ),
            MatchResult(zotero_key='Z3', title='Failed', matched=False, error='Error', candidates=[]),
            MatchResult(zotero_key='Z4', title='Auto2', matched=True, paper_id='W333')
        ]
        
        mock_reviewer.review.return_value = 'W222'
        
        paper_ids = presenter.present(results, mock_reviewer)
        
        assert paper_ids == ['W111', 'W333', 'W222']
        assert mock_reviewer.review.call_count == 1