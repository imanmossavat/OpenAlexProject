

import pytest
from ArticleCrawler.api.zotero.metadata_extractor import ZoteroMetadataExtractor


@pytest.mark.unit
class TestZoteroMetadataExtractor:
    
    @pytest.fixture
    def extractor(self):
        return ZoteroMetadataExtractor()
    
    @pytest.fixture
    def sample_item(self):
        return {
            'data': {
                'key': 'ITEM123',
                'title': 'Test Paper Title',
                'creators': [
                    {'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'},
                    {'creatorType': 'author', 'firstName': 'Jane', 'lastName': 'Smith'},
                    {'creatorType': 'editor', 'firstName': 'Bob', 'lastName': 'Editor'}
                ],
                'date': '2024-01-15',
                'publicationTitle': 'Test Journal',
                'DOI': '10.1234/test.2024.001',
                'url': 'https://example.com/paper',
                'abstractNote': 'This is a test abstract.',
                'tags': [{'tag': 'machine learning'}, {'tag': 'AI'}],
                'itemType': 'journalArticle'
            }
        }
    
    def test_extract_complete_metadata(self, extractor, sample_item):
        """Test extraction with complete metadata."""
        result = extractor.extract(sample_item)
        
        assert result['title'] == 'Test Paper Title'
        assert result['authors'] == ['John Doe', 'Jane Smith']
        assert result['date'] == '2024-01-15'
        assert result['year'] == 2024
        assert result['publication'] == 'Test Journal'
        assert result['doi'] == '10.1234/test.2024.001'
        assert result['url'] == 'https://example.com/paper'
        assert result['abstract'] == 'This is a test abstract.'
        assert result['tags'] == ['machine learning', 'AI']
        assert result['item_type'] == 'journalArticle'
        assert result['zotero_key'] == 'ITEM123'
    
    def test_extract_minimal_metadata(self, extractor):
        """Test extraction with minimal metadata."""
        minimal_item = {
            'data': {
                'key': 'ITEM456',
                'title': 'Minimal Paper'
            }
        }
        
        result = extractor.extract(minimal_item)
        
        assert result['title'] == 'Minimal Paper'
        assert result['authors'] == []
        assert result['date'] == ''
        assert result['year'] is None
        assert result['publication'] == ''
        assert result['doi'] == ''
        assert result['url'] == ''
        assert result['abstract'] == ''
        assert result['tags'] == []
        assert result['item_type'] == ''
        assert result['zotero_key'] == 'ITEM456'
    
    def test_extract_no_title(self, extractor):
        """Test extraction when title is missing."""
        item = {'data': {'key': 'ITEM789'}}
        
        result = extractor.extract(item)
        
        assert result['title'] == 'Untitled'
    
    def test_extract_authors_first_name_only(self, extractor):
        """Test author extraction with only first name."""
        item = {
            'data': {
                'key': 'ITEM999',
                'creators': [
                    {'creatorType': 'author', 'firstName': 'John', 'lastName': ''}
                ]
            }
        }
        
        result = extractor.extract(item)
        
        assert result['authors'] == []
    
    def test_extract_authors_last_name_only(self, extractor):
        """Test author extraction with only last name."""
        item = {
            'data': {
                'key': 'ITEM999',
                'creators': [
                    {'creatorType': 'author', 'firstName': '', 'lastName': 'Doe'}
                ]
            }
        }
        
        result = extractor.extract(item)
        
        assert result['authors'] == ['Doe']
    
    def test_extract_authors_filters_non_authors(self, extractor):
        """Test that only authors are extracted, not editors etc."""
        item = {
            'data': {
                'key': 'ITEM888',
                'creators': [
                    {'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'},
                    {'creatorType': 'editor', 'firstName': 'Jane', 'lastName': 'Editor'},
                    {'creatorType': 'translator', 'firstName': 'Bob', 'lastName': 'Translator'}
                ]
            }
        }
        
        result = extractor.extract(item)
        
        assert result['authors'] == ['John Doe']
    
    def test_extract_year_from_various_date_formats(self, extractor):
        """Test year extraction from different date formats."""
        test_cases = [
            ('2024', 2024),
            ('2024-01-15', 2024),
            ('01/15/2024', 2024),
            ('January 15, 2024', 2024),
            ('2024-01', 2024),
            ('1999', 1999),
            ('2000', 2000),
            ('no year here', None),
            ('', None),
        ]
        
        for date_str, expected_year in test_cases:
            result = extractor._extract_year(date_str)
            assert result == expected_year, f"Failed for date: {date_str}"
    
    def test_extract_year_invalid_year(self, extractor):
        """Test year extraction with invalid year."""
        assert extractor._extract_year('1899') is None
        assert extractor._extract_year('2100') is None
        assert extractor._extract_year('3000') is None
    
    def test_extract_with_empty_data(self, extractor):
        """Test extraction with empty data dictionary."""
        item = {'data': {}}
        
        result = extractor.extract(item)
        
        assert result['title'] == 'Untitled'
        assert result['authors'] == []
        assert result['zotero_key'] == ''