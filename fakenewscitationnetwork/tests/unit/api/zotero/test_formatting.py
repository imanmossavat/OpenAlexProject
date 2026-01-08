
import pytest
from ArticleCrawler.api.zotero.formatting import ZoteroItemFormatter


@pytest.mark.unit
class TestZoteroItemFormatter:
    
    @pytest.fixture
    def formatter(self):
        return ZoteroItemFormatter()
    
    @pytest.fixture
    def complete_metadata(self):
        return {
            'title': 'Test Paper Title',
            'authors': ['John Doe', 'Jane Smith'],
            'date': '2024-01-15',
            'publication': 'Test Journal',
            'doi': '10.1234/test.2024.001',
            'url': 'https://example.com/paper',
            'abstract': 'This is a test abstract for testing formatting.',
            'tags': ['machine learning', 'AI']
        }
    
    def test_format_collection_preview_complete(self, formatter, complete_metadata):
        """Test preview formatting with complete metadata."""
        result = formatter.format_collection_preview(complete_metadata)
        
        assert 'Test Paper Title' in result
        assert 'John Doe, Jane Smith' in result
        assert '2024-01-15' in result
        assert 'Test Journal' in result
        assert '10.1234/test.2024.001' in result
    
    def test_format_collection_preview_minimal(self, formatter):
        """Test preview formatting with minimal metadata."""
        minimal_metadata = {
            'title': 'Minimal Paper',
            'authors': [],
            'date': '',
            'publication': '',
            'doi': '',
            'url': '',
            'abstract': '',
            'tags': []
        }
        
        result = formatter.format_collection_preview(minimal_metadata)
        
        assert 'Minimal Paper' in result
        assert 'N/A' in result
    
    def test_format_collection_preview_no_date_or_publication(self, formatter):
        """Test preview formatting without date or publication."""
        metadata = {
            'title': 'Paper Without Date',
            'authors': ['Author Name'],
            'date': '',
            'publication': '',
            'doi': '10.1234/test',
            'url': '',
            'abstract': '',
            'tags': []
        }
        
        result = formatter.format_collection_preview(metadata)
        
        assert 'Paper Without Date' in result
        assert 'Author Name' in result
        assert '10.1234/test' in result
    
    def test_format_detailed_complete(self, formatter, complete_metadata):
        """Test detailed formatting with complete metadata."""
        result = formatter.format_detailed(complete_metadata)
        
        assert 'Title: Test Paper Title' in result
        assert 'Authors: John Doe, Jane Smith' in result
        assert 'Date: 2024-01-15' in result
        assert 'Publication: Test Journal' in result
        assert 'DOI: 10.1234/test.2024.001' in result
        assert 'URL: https://example.com/paper' in result
        assert 'Tags: machine learning, AI' in result
        assert 'Abstract:' in result
        assert 'This is a test abstract' in result
        assert '-' * 60 in result
    
    def test_format_detailed_minimal(self, formatter):
        """Test detailed formatting with minimal metadata."""
        minimal_metadata = {
            'title': 'Minimal Paper',
            'authors': [],
            'date': '',
            'publication': '',
            'doi': '',
            'url': '',
            'abstract': '',
            'tags': []
        }
        
        result = formatter.format_detailed(minimal_metadata)
        
        assert 'Title: Minimal Paper' in result
        assert 'Authors: N/A' in result
        assert 'Tags: None' in result
    
    def test_format_detailed_long_abstract(self, formatter):
        """Test detailed formatting truncates long abstracts."""
        long_abstract = 'A' * 600
        metadata = {
            'title': 'Paper With Long Abstract',
            'authors': ['Author'],
            'date': '2024',
            'publication': 'Journal',
            'doi': '',
            'url': '',
            'abstract': long_abstract,
            'tags': []
        }
        
        result = formatter.format_detailed(metadata)
        
        assert '...' in result
        assert len(result) < len(long_abstract) + 500
    
    def test_format_detailed_no_abstract(self, formatter):
        """Test detailed formatting without abstract."""
        metadata = {
            'title': 'No Abstract Paper',
            'authors': ['Author'],
            'date': '2024',
            'publication': 'Journal',
            'doi': '10.1234/test',
            'url': '',
            'abstract': '',
            'tags': []
        }
        
        result = formatter.format_detailed(metadata)
        
        assert 'Title: No Abstract Paper' in result
    
    def test_format_detailed_no_url(self, formatter):
        """Test detailed formatting without URL."""
        metadata = {
            'title': 'Paper',
            'authors': ['Author'],
            'date': '2024',
            'publication': 'Journal',
            'doi': '10.1234/test',
            'url': '',
            'abstract': 'Abstract text',
            'tags': []
        }
        
        result = formatter.format_detailed(metadata)
        
        assert 'Title: Paper' in result
        assert result.count('🌐 URL:') == 0 or 'URL: ' not in result