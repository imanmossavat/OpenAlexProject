
import pytest
from unittest.mock import Mock, patch, MagicMock
from ArticleCrawler.api.openalex_api import OpenAlexAPIProvider


@pytest.mark.unit
class TestOpenAlexAPIExtensions:
    
    @pytest.fixture
    def openalex_provider(self, mock_logger, monkeypatch):
        monkeypatch.setenv('OPENALEX_EMAIL', 'test@example.com')
        return OpenAlexAPIProvider(retries=1, logger=mock_logger)
    
    @pytest.fixture
    def mock_work_response(self):
        return {
            'id': 'https://openalex.org/W2134567890',
            'title': 'Test Paper',
            'abstract_inverted_index': {'test': [0], 'abstract': [1]},
            'publication_year': 2024,
            'doi': 'https://doi.org/10.1234/test',
            'primary_location': {'source': {'display_name': 'Test Venue'}},
            'authorships': [
                {'author': {'id': 'https://openalex.org/A123', 'display_name': 'Test Author'}}
            ],
            'referenced_works': ['https://openalex.org/W999'],
            'cited_by_count': 10,
            'concepts': [
                {'id': 'https://openalex.org/C123', 'display_name': 'Machine Learning', 'level': 2, 'score': 0.95}
            ],
            'topics': [
                {'id': 'https://openalex.org/T123', 'display_name': 'Deep Learning', 'score': 0.9}
            ],
            'subfields': [
                {'id': 'https://openalex.org/subfields/1702', 'display_name': 'Artificial Intelligence'}
            ],
            'fields': [
                {'id': 'https://openalex.org/fields/17', 'display_name': 'Computer Science'}
            ],
            'domains': [
                {'id': 'https://openalex.org/domains/3', 'display_name': 'Physical Sciences'}
            ]
        }
    
    @patch('ArticleCrawler.api.openalex_api.Works')
    def test_get_paper_metadata_only_success(self, mock_works, openalex_provider, mock_work_response):
        mock_works_instance = MagicMock()
        mock_works_instance.__getitem__.return_value = mock_work_response
        mock_works.return_value = mock_works_instance
        
        result = openalex_provider.get_paper_metadata_only('W2134567890')
        
        assert result is not None
        assert result['id'] == 'https://openalex.org/W2134567890'
        assert result['title'] == 'Test Paper'
    
    @patch('ArticleCrawler.api.openalex_api.Works')
    def test_get_paper_metadata_only_failure(self, mock_works, openalex_provider):
        mock_works_instance = MagicMock()
        mock_works_instance.__getitem__.side_effect = Exception("API Error")
        mock_works.return_value = mock_works_instance
        
        result = openalex_provider.get_paper_metadata_only('W9999')
        
        assert result is None
        assert 'W9999' in openalex_provider.failed_paper_ids
    
    @patch('ArticleCrawler.api.openalex_api.Works')
    def test_get_papers_batch_success(self, mock_works, openalex_provider, mock_work_response):
        mock_works_instance = MagicMock()
        mock_works_instance.filter.return_value = mock_works_instance
        mock_works_instance.get.return_value = [mock_work_response]
        mock_works.return_value = mock_works_instance
        
        paper_ids = ['W2134567890', 'W9876543210']
        results = openalex_provider.get_papers_batch(paper_ids)
        
        assert len(results) == 1
        assert results[0]['id'] == 'https://openalex.org/W2134567890'
    
    @patch('ArticleCrawler.api.openalex_api.Works')
    def test_get_papers_batch_empty(self, mock_works, openalex_provider):
        mock_works_instance = MagicMock()
        mock_works_instance.filter.return_value = mock_works_instance
        mock_works_instance.get.return_value = []
        mock_works.return_value = mock_works_instance
        
        results = openalex_provider.get_papers_batch(['W9999'])
        
        assert results == []
    
    @patch('ArticleCrawler.api.openalex_api.Works')
    def test_get_paper_as_paper_data_success(self, mock_works, openalex_provider, mock_work_response):
        mock_works_instance = MagicMock()
        mock_works_instance.__getitem__.return_value = mock_work_response
        mock_works.return_value = mock_works_instance
        
        paper_data = openalex_provider.get_paper_as_paper_data('W2134567890')
        
        assert paper_data is not None
        assert paper_data.paper_id == 'W2134567890'
        assert paper_data.title == 'Test Paper'
        assert paper_data.year == 2024
        assert paper_data.venue == 'Test Venue'
        assert paper_data.abstract == 'test abstract'
        assert len(paper_data.authors) == 1
        assert paper_data.authors[0]['name'] == 'Test Author'
    
    @patch('ArticleCrawler.api.openalex_api.Works')
    def test_get_paper_as_paper_data_failure(self, mock_works, openalex_provider):
        mock_works_instance = MagicMock()
        mock_works_instance.__getitem__.side_effect = Exception("API Error")
        mock_works.return_value = mock_works_instance
        
        paper_data = openalex_provider.get_paper_as_paper_data('W9999')
        
        assert paper_data is None
        assert 'W9999' in openalex_provider.failed_paper_ids
    
    def test_convert_work_to_paper_data_complete(self, openalex_provider, mock_work_response):
        paper_data = openalex_provider._convert_work_to_paper_data(mock_work_response)
        
        assert paper_data.paper_id == 'W2134567890'
        assert paper_data.title == 'Test Paper'
        assert paper_data.year == 2024
        assert paper_data.venue == 'Test Venue'
        assert paper_data.doi == '10.1234/test'
        assert paper_data.url == 'https://openalex.org/W2134567890'
        assert len(paper_data.concepts) >= 0
        assert len(paper_data.topics) >= 0
        assert len(paper_data.subfields) >= 0
        assert len(paper_data.fields) >= 0
        assert len(paper_data.domains) >= 0
    
    def test_convert_work_to_paper_data_minimal(self, openalex_provider):
        minimal_work = {
            'id': 'https://openalex.org/W123',
            'title': 'Minimal Paper',
            'publication_year': None,
            'doi': None,
            'primary_location': None,
            'abstract_inverted_index': None,
            'authorships': [],
            'concepts': [],
            'topics': [],
            'subfields': [],
            'fields': [],
            'domains': []
        }
        
        paper_data = openalex_provider._convert_work_to_paper_data(minimal_work)
        
        assert paper_data.paper_id == 'W123'
        assert paper_data.title == 'Minimal Paper'
        assert paper_data.year is None
        assert paper_data.venue is None
        assert paper_data.abstract is None or paper_data.abstract == ''
        assert paper_data.authors == []
        assert paper_data.concepts == []
    
    def test_extract_hierarchy_from_concepts(self, openalex_provider):
        concepts = [
            {'id': 'C1', 'display_name': 'AI', 'level': 0, 'score': 0.9},
            {'id': 'C2', 'display_name': 'ML', 'level': 1, 'score': 0.8},
            {'id': 'C3', 'display_name': 'DL', 'level': 2, 'score': 0.7}
        ]
        
        hierarchy = openalex_provider._extract_hierarchy_from_concepts(concepts)
        
        assert 'domains' in hierarchy
        assert 'fields' in hierarchy
        assert 'subfields' in hierarchy
    
    def test_extract_hierarchy_empty_concepts(self, openalex_provider):
        hierarchy = openalex_provider._extract_hierarchy_from_concepts([])
        
        assert 'domains' in hierarchy
        assert 'fields' in hierarchy
        assert 'subfields' in hierarchy
        assert isinstance(hierarchy['domains'], list)
        assert isinstance(hierarchy['fields'], list)
        assert isinstance(hierarchy['subfields'], list)
    
    def test_reconstruct_abstract_complex(self, openalex_provider):
        inverted_index = {
            'This': [0, 5],
            'is': [1],
            'a': [2],
            'test': [3, 6],
            'abstract': [4]
        }
        
        result = openalex_provider._reconstruct_abstract(inverted_index)
        
        assert 'This' in result
        assert 'test' in result
        assert 'abstract' in result
    
    def test_reconstruct_abstract_empty(self, openalex_provider):
        result = openalex_provider._reconstruct_abstract({})
        
        assert result == '' or result is None
    
    def test_reconstruct_abstract_none(self, openalex_provider):
        result = openalex_provider._reconstruct_abstract(None)
        
        assert result == '' or result is None