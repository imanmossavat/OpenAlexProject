

import pytest
from unittest.mock import Mock, patch, MagicMock
from ArticleCrawler.cli.zotero.workflow import ZoteroSeedWorkflow


@pytest.mark.unit
class TestZoteroSeedWorkflow:
    
    @pytest.fixture
    def mock_prompter(self):
        return Mock()
    
    @pytest.fixture
    def mock_console(self):
        console = Mock()
        console.status.return_value.__enter__ = Mock()
        console.status.return_value.__exit__ = Mock()
        return console
    
    @pytest.fixture
    def mock_client(self, monkeypatch):
        """Mock ZoteroClient."""
        mock = Mock()
        mock_class = Mock(return_value=mock)
        monkeypatch.setattr('ArticleCrawler.cli.zotero.workflow.ZoteroClient', mock_class)
        return mock
    
    @pytest.fixture
    def mock_components(self, monkeypatch):
        """Mock all UI components."""
        mocks = {
            'collection_selector': Mock(),
            'mode_chooser': Mock(),
            'paper_selector': Mock(),
            'match_reviewer': Mock(),
            'results_presenter': Mock()
        }
        
        monkeypatch.setattr('ArticleCrawler.cli.zotero.workflow.ZoteroCollectionSelector', Mock(return_value=mocks['collection_selector']))
        monkeypatch.setattr('ArticleCrawler.cli.zotero.workflow.SelectionModeChooser', Mock(return_value=mocks['mode_chooser']))
        monkeypatch.setattr('ArticleCrawler.cli.zotero.workflow.PaperSelector', Mock(return_value=mocks['paper_selector']))
        monkeypatch.setattr('ArticleCrawler.cli.zotero.workflow.MatchReviewer', Mock(return_value=mocks['match_reviewer']))
        monkeypatch.setattr('ArticleCrawler.cli.zotero.workflow.MatchResultsPresenter', Mock(return_value=mocks['results_presenter']))
        
        return mocks
    
    @pytest.fixture
    def workflow(self, mock_prompter, mock_console, mock_client, mock_components):
        """Create workflow instance with mocked dependencies."""
        return ZoteroSeedWorkflow(
            prompter=mock_prompter,
            console=mock_console,
            api_provider_type='openalex'
        )
    
    def test_init_success(self, mock_prompter, mock_console, mock_client, mock_components):
        """Test successful initialization."""
        workflow = ZoteroSeedWorkflow(
            prompter=mock_prompter,
            console=mock_console,
            api_provider_type='openalex'
        )
        
        assert workflow.prompter == mock_prompter
        assert workflow.console == mock_console
        assert workflow.api_provider_type == 'openalex'
        assert workflow.client == mock_client
    
    def test_init_client_error(self, mock_prompter, mock_console, monkeypatch):
        """Test initialization handles client errors."""
        mock_client_class = Mock(side_effect=ValueError("Missing API key"))
        monkeypatch.setattr('ArticleCrawler.cli.zotero.workflow.ZoteroClient', mock_client_class)
        
        with pytest.raises(ValueError, match="Missing API key"):
            ZoteroSeedWorkflow(
                prompter=mock_prompter,
                console=mock_console,
                api_provider_type='openalex'
            )
        
        mock_prompter.error.assert_called_once()
    
    def test_execute_full_workflow_all_mode(self, workflow, mock_client, mock_components):
        """Test complete workflow with 'all' mode."""
        collections = [{'key': 'COL1', 'name': 'My Collection'}]
        items_metadata = [
            {'zotero_key': 'Z1', 'title': 'Paper 1', 'doi': '10.1234/1'},
            {'zotero_key': 'Z2', 'title': 'Paper 2', 'doi': '10.1234/2'}
        ]
        
        mock_client.get_collections.return_value = collections
        mock_client.get_collection_items.return_value = [Mock(), Mock()]
        
        mock_components['collection_selector'].select.return_value = collections[0]
        mock_components['mode_chooser'].choose.return_value = 'all'
        mock_components['results_presenter'].present.return_value = ['W123', 'W456']
        
        with patch.object(workflow, '_load_items', return_value=items_metadata), \
             patch.object(workflow, '_match_papers', return_value=['W123', 'W456']):
            
            result = workflow.execute()
        
        assert result == ['W123', 'W456']
        mock_components['collection_selector'].select.assert_called_once()
        mock_components['mode_chooser'].choose.assert_called_once()
        mock_components['paper_selector'].select.assert_not_called()
    
    def test_execute_full_workflow_individual_mode(self, workflow, mock_client, mock_components):
        """Test complete workflow with 'individual' mode."""
        collections = [{'key': 'COL1', 'name': 'My Collection'}]
        items_metadata = [
            {'zotero_key': 'Z1', 'title': 'Paper 1', 'doi': '10.1234/1'},
            {'zotero_key': 'Z2', 'title': 'Paper 2', 'doi': '10.1234/2'}
        ]
        selected_items = [items_metadata[0]]
        
        mock_client.get_collections.return_value = collections
        
        mock_components['collection_selector'].select.return_value = collections[0]
        mock_components['mode_chooser'].choose.return_value = 'individual'
        mock_components['paper_selector'].select.return_value = selected_items
        mock_components['results_presenter'].present.return_value = ['W123']
        
        with patch.object(workflow, '_load_items', return_value=items_metadata), \
             patch.object(workflow, '_match_papers', return_value=['W123']):
            
            result = workflow.execute()
        
        assert result == ['W123']
        mock_components['paper_selector'].select.assert_called_once_with(items_metadata)
    
    def test_execute_no_collections(self, workflow, mock_client, mock_prompter):
        """Test execute handles no collections."""
        mock_client.get_collections.return_value = []
        
        result = workflow.execute()
        
        assert result == []
        mock_prompter.error.assert_called_with("No collections found")
    
    def test_execute_no_collection_selected(self, workflow, mock_client, mock_components):
        """Test execute handles user canceling collection selection."""
        collections = [{'key': 'COL1', 'name': 'My Collection'}]
        mock_client.get_collections.return_value = collections
        mock_components['collection_selector'].select.return_value = None
        
        result = workflow.execute()
        
        assert result == []
    
    def test_execute_no_items_in_collection(self, workflow, mock_client, mock_components, mock_prompter):
        """Test execute handles empty collection."""
        collections = [{'key': 'COL1', 'name': 'My Collection'}]
        mock_client.get_collections.return_value = collections
        mock_components['collection_selector'].select.return_value = collections[0]
        
        with patch.object(workflow, '_load_items', return_value=[]):
            result = workflow.execute()
        
        assert result == []
        mock_prompter.error.assert_called_with("No bibliographic items found")
    
    def test_execute_no_papers_selected(self, workflow, mock_client, mock_components):
        """Test execute handles no papers selected in individual mode."""
        collections = [{'key': 'COL1', 'name': 'My Collection'}]
        items_metadata = [
            {'zotero_key': 'Z1', 'title': 'Paper 1', 'doi': '10.1234/1'}
        ]
        
        mock_client.get_collections.return_value = collections
        mock_components['collection_selector'].select.return_value = collections[0]
        mock_components['mode_chooser'].choose.return_value = 'individual'
        mock_components['paper_selector'].select.return_value = []
        
        with patch.object(workflow, '_load_items', return_value=items_metadata):
            result = workflow.execute()
        
        assert result == []
    
    def test_load_collections_success(self, workflow, mock_client):
        """Test successful collection loading."""
        collections = [
            {'key': 'COL1', 'name': 'Collection 1'},
            {'key': 'COL2', 'name': 'Collection 2'}
        ]
        mock_client.get_collections.return_value = collections
        
        result = workflow._load_collections()
        
        assert result == collections
        mock_client.get_collections.assert_called_once()
    
    def test_load_collections_error(self, workflow, mock_client, mock_prompter):
        """Test collection loading handles errors."""
        mock_client.get_collections.side_effect = Exception("API Error")
        
        result = workflow._load_collections()
        
        assert result == []
        mock_prompter.error.assert_called_once()
    
    def test_load_items_success(self, workflow, mock_client):
        """Test successful item loading."""
        collection = {'key': 'COL1', 'name': 'My Collection'}
        items = [
            {'data': {'key': 'ITEM1', 'title': 'Paper 1'}},
            {'data': {'key': 'ITEM2', 'title': 'Paper 2'}}
        ]
        mock_client.get_collection_items.return_value = items
        
        result = workflow._load_items(collection)
        
        assert len(result) == 2
        mock_client.get_collection_items.assert_called_once_with('COL1')
    
    def test_load_items_error(self, workflow, mock_client, mock_prompter):
        """Test item loading handles errors."""
        collection = {'key': 'COL1', 'name': 'My Collection'}
        mock_client.get_collection_items.side_effect = Exception("API Error")
        
        result = workflow._load_items(collection)
        
        assert result == []
        mock_prompter.error.assert_called_once()
    
    @patch('ArticleCrawler.cli.zotero.workflow.create_api_provider')
    @patch('ArticleCrawler.cli.zotero.workflow.ZoteroMatcher')
    def test_match_papers_success(self, mock_matcher_class, mock_create_api, workflow):
        """Test successful paper matching."""
        mock_api = Mock()
        mock_create_api.return_value = mock_api
        
        mock_matcher = Mock()
        mock_matcher_class.return_value = mock_matcher
        
        match_results = [
            Mock(matched=True, paper_id='W123'),
            Mock(matched=True, paper_id='W456')
        ]
        mock_matcher.match_items.return_value = match_results
        
        items_metadata = [
            {'zotero_key': 'Z1', 'title': 'Paper 1'},
            {'zotero_key': 'Z2', 'title': 'Paper 2'}
        ]
        
        workflow.match_reviewer = Mock()
        workflow.results_presenter.present.return_value = ['W123', 'W456']
        
        result = workflow._match_papers(items_metadata)
        
        assert result == ['W123', 'W456']
        mock_create_api.assert_called_once_with('openalex')
        mock_matcher_class.assert_called_once_with(mock_api)
        mock_matcher.match_items.assert_called_once_with(items_metadata)
    
    @patch('ArticleCrawler.cli.zotero.workflow.create_api_provider')
    @patch('ArticleCrawler.cli.zotero.workflow.ZoteroMatcher')
    def test_match_papers_no_matches(self, mock_matcher_class, mock_create_api, workflow, mock_prompter):
        """Test paper matching with no successful matches."""
        mock_api = Mock()
        mock_create_api.return_value = mock_api
        
        mock_matcher = Mock()
        mock_matcher_class.return_value = mock_matcher
        mock_matcher.match_items.return_value = []
        
        workflow.results_presenter.present.return_value = []
        
        items_metadata = [{'zotero_key': 'Z1', 'title': 'Paper 1'}]
        
        result = workflow._match_papers(items_metadata)
        
        assert result == []
        mock_prompter.warning.assert_called_once()