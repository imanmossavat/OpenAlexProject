

import pytest
from unittest.mock import Mock, patch, MagicMock
from ArticleCrawler.api.zotero.client import ZoteroClient


@pytest.mark.unit
class TestZoteroClient:
    
    @pytest.fixture
    def mock_zotero_class(self):
        """Mock pyzotero.zotero.Zotero class."""
        mock_zot = Mock()
        return Mock(return_value=mock_zot), mock_zot
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    @patch('ArticleCrawler.api.zotero.client.zotero.Zotero')
    def test_init_success(self, mock_zotero_class, mock_getenv, mock_load_dotenv, mock_logger):
        """Test successful initialization."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': '12345',
            'ZOTERO_LIBRARY_TYPE': 'user',
            'ZOTERO_API_KEY': 'test_api_key'
        }.get(key, default)
        
        mock_zot = Mock()
        mock_zotero_class.return_value = mock_zot
        
        client = ZoteroClient(logger=mock_logger)
        
        assert client.library_id == '12345'
        assert client.library_type == 'user'
        assert client.api_key == 'test_api_key'
        assert client.zot == mock_zot
        mock_zotero_class.assert_called_once_with('12345', 'user', 'test_api_key')
        mock_logger.info.assert_called_once()
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    def test_init_missing_library_id(self, mock_getenv, mock_load_dotenv):
        """Test initialization fails without library ID."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': None,
            'ZOTERO_API_KEY': 'test_api_key'
        }.get(key, default)
        
        with pytest.raises(ValueError, match="ZOTERO_LIBRARY_ID and ZOTERO_API_KEY must be set"):
            ZoteroClient()
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    def test_init_missing_api_key(self, mock_getenv, mock_load_dotenv):
        """Test initialization fails without API key."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': '12345',
            'ZOTERO_API_KEY': None
        }.get(key, default)
        
        with pytest.raises(ValueError, match="ZOTERO_LIBRARY_ID and ZOTERO_API_KEY must be set"):
            ZoteroClient()
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    @patch('ArticleCrawler.api.zotero.client.zotero.Zotero')
    def test_rate_limit_enforces_delay(self, mock_zotero_class, mock_getenv, mock_load_dotenv, mock_logger):
        """Test rate limiting enforces minimum delay."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': '12345',
            'ZOTERO_LIBRARY_TYPE': 'user',
            'ZOTERO_API_KEY': 'test_api_key'
        }.get(key, default)
        
        mock_zot = Mock()
        mock_zotero_class.return_value = mock_zot
        
        client = ZoteroClient(logger=mock_logger)
        client.min_delay = 0.1
        
        import time
        start = time.time()
        client._rate_limit()
        client._rate_limit()
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    @patch('ArticleCrawler.api.zotero.client.zotero.Zotero')
    def test_get_collections_success(self, mock_zotero_class, mock_getenv, mock_load_dotenv, mock_logger):
        """Test successful collection retrieval."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': '12345',
            'ZOTERO_LIBRARY_TYPE': 'user',
            'ZOTERO_API_KEY': 'test_api_key'
        }.get(key, default)
        
        mock_zot = Mock()
        mock_zotero_class.return_value = mock_zot
        
        mock_collections = [
            {'data': {'key': 'ABC123', 'name': 'Collection 1'}},
            {'data': {'key': 'DEF456', 'name': 'Collection 2'}}
        ]
        mock_zot.collections.return_value = mock_collections
        
        client = ZoteroClient(logger=mock_logger)
        client.min_delay = 0
        
        result = client.get_collections()
        
        assert len(result) == 2
        assert result[0]['key'] == 'ABC123'
        assert result[0]['name'] == 'Collection 1'
        assert result[1]['key'] == 'DEF456'
        assert result[1]['name'] == 'Collection 2'
        mock_zot.collections.assert_called_once()
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    @patch('ArticleCrawler.api.zotero.client.zotero.Zotero')
    def test_get_collections_empty(self, mock_zotero_class, mock_getenv, mock_load_dotenv, mock_logger):
        """Test collection retrieval with no collections."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': '12345',
            'ZOTERO_LIBRARY_TYPE': 'user',
            'ZOTERO_API_KEY': 'test_api_key'
        }.get(key, default)
        
        mock_zot = Mock()
        mock_zotero_class.return_value = mock_zot
        mock_zot.collections.return_value = []
        
        client = ZoteroClient(logger=mock_logger)
        client.min_delay = 0
        
        result = client.get_collections()
        
        assert result == []
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    @patch('ArticleCrawler.api.zotero.client.zotero.Zotero')
    def test_get_collections_error(self, mock_zotero_class, mock_getenv, mock_load_dotenv, mock_logger):
        """Test collection retrieval handles errors."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': '12345',
            'ZOTERO_LIBRARY_TYPE': 'user',
            'ZOTERO_API_KEY': 'test_api_key'
        }.get(key, default)
        
        mock_zot = Mock()
        mock_zotero_class.return_value = mock_zot
        mock_zot.collections.side_effect = Exception("API Error")
        
        client = ZoteroClient(logger=mock_logger)
        client.min_delay = 0
        
        with pytest.raises(Exception, match="API Error"):
            client.get_collections()
        
        mock_logger.error.assert_called_once()
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    @patch('ArticleCrawler.api.zotero.client.zotero.Zotero')
    def test_get_collection_items_success(self, mock_zotero_class, mock_getenv, mock_load_dotenv, mock_logger):
        """Test successful item retrieval from collection."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': '12345',
            'ZOTERO_LIBRARY_TYPE': 'user',
            'ZOTERO_API_KEY': 'test_api_key'
        }.get(key, default)
        
        mock_zot = Mock()
        mock_zotero_class.return_value = mock_zot
        
        mock_items = [
            {'data': {'itemType': 'journalArticle', 'title': 'Paper 1'}},
            {'data': {'itemType': 'attachment', 'title': 'PDF'}},
            {'data': {'itemType': 'conferencePaper', 'title': 'Paper 2'}},
            {'data': {'itemType': 'note', 'title': 'My Notes'}}
        ]
        mock_zot.collection_items.return_value = mock_items
        
        client = ZoteroClient(logger=mock_logger)
        client.min_delay = 0
        
        result = client.get_collection_items('ABC123')
        
        assert len(result) == 2
        assert result[0]['data']['title'] == 'Paper 1'
        assert result[1]['data']['title'] == 'Paper 2'
        mock_zot.collection_items.assert_called_once_with('ABC123')
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    @patch('ArticleCrawler.api.zotero.client.zotero.Zotero')
    def test_get_collection_items_empty(self, mock_zotero_class, mock_getenv, mock_load_dotenv, mock_logger):
        """Test item retrieval with no items."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': '12345',
            'ZOTERO_LIBRARY_TYPE': 'user',
            'ZOTERO_API_KEY': 'test_api_key'
        }.get(key, default)
        
        mock_zot = Mock()
        mock_zotero_class.return_value = mock_zot
        mock_zot.collection_items.return_value = []
        
        client = ZoteroClient(logger=mock_logger)
        client.min_delay = 0
        
        result = client.get_collection_items('ABC123')
        
        assert result == []
    
    @patch('ArticleCrawler.api.zotero.client.load_dotenv')
    @patch('ArticleCrawler.api.zotero.client.os.getenv')
    @patch('ArticleCrawler.api.zotero.client.zotero.Zotero')
    def test_get_collection_items_error(self, mock_zotero_class, mock_getenv, mock_load_dotenv, mock_logger):
        """Test item retrieval handles errors."""
        mock_getenv.side_effect = lambda key, default=None: {
            'ZOTERO_LIBRARY_ID': '12345',
            'ZOTERO_LIBRARY_TYPE': 'user',
            'ZOTERO_API_KEY': 'test_api_key'
        }.get(key, default)
        
        mock_zot = Mock()
        mock_zotero_class.return_value = mock_zot
        mock_zot.collection_items.side_effect = Exception("API Error")
        
        client = ZoteroClient(logger=mock_logger)
        client.min_delay = 0
        
        with pytest.raises(Exception, match="API Error"):
            client.get_collection_items('ABC123')
        
        mock_logger.error.assert_called_once()