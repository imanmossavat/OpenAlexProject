import pytest
from unittest.mock import Mock
from ArticleCrawler.api.base_api import BaseAPIProvider


@pytest.mark.unit
class TestBaseAPIProvider:
    
    def test_base_api_is_abstract(self):
        with pytest.raises(TypeError):
            BaseAPIProvider()
    
    def test_get_paper_is_abstract_method(self):
        class IncompleteProvider(BaseAPIProvider):
            pass
        
        with pytest.raises(TypeError):
            IncompleteProvider()
    
    def test_concrete_implementation_works(self):
        class ConcreteProvider(BaseAPIProvider):
            def get_paper(self, paper_id: str):
                return None
            
            def get_papers(self, paper_ids):
                return []
            
            def get_author_papers(self, author_id: str):
                return [], []
            
            def get_failed_and_inconsistent_papers(self):
                return {'failed': [], 'inconsistent': []}
            
            @property
            def failed_paper_ids(self):
                return []
            
            @property
            def inconsistent_api_response_paper_ids(self):
                return []
        
        provider = ConcreteProvider()
        assert provider is not None
        assert provider.get_paper('test') is None
        assert provider.get_papers(['test']) == []