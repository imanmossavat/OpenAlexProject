import pytest
from unittest.mock import Mock
from ArticleCrawler.data.paper_validator import PaperValidator


@pytest.mark.unit
class TestPaperValidator:
    
    def test_check_papers_with_valid_paper_processed_true(self, paper_validator):
        paper = Mock()
        paper.paperId = 'W123'
        paper.title = 'Test Paper'
        paper.abstract = 'Test abstract'
        
        result = paper_validator.checkPapers([paper], processed=True)
        assert len(result) == 1
        assert result[0].paperId == 'W123'
    
    def test_check_papers_rejects_paper_without_abstract_when_processed(self, paper_validator):
        paper = Mock()
        paper.paperId = 'W123'
        paper.title = 'Test Paper'
        
        delattr(paper, 'abstract')
        
        result = paper_validator.checkPapers([paper], processed=True)
        assert len(result) == 0
    
    def test_check_papers_accepts_paper_without_abstract_when_not_processed(self, paper_validator):
        paper = Mock()
        paper.paperId = 'W123'
        paper.title = 'Test Paper'
        
        result = paper_validator.checkPapers([paper], processed=False)
        assert len(result) == 1
    
    def test_check_papers_rejects_paper_without_paper_id(self, paper_validator):
        paper = Mock()
        paper.paperId = None
        paper.title = 'Test Paper'
        
        result = paper_validator.checkPapers([paper], processed=False)
        assert len(result) == 0
    
    def test_check_papers_rejects_paper_with_empty_paper_id(self, paper_validator):
        paper = Mock()
        paper.paperId = ''
        paper.title = 'Test Paper'
        
        result = paper_validator.checkPapers([paper], processed=False)
        assert len(result) == 0
    
    def test_check_papers_openalex_accepts_paper_without_abstract(self, paper_validator):
        paper = Mock()
        paper.paperId = 'W123'
        paper.title = 'Test Paper'
        paper.abstract = None
        
        result = paper_validator.checkPapersOpenAlex([paper], processed=True)
        assert len(result) == 1
    
    def test_check_papers_openalex_validates_paper_id_string(self, paper_validator):
        paper = Mock()
        paper.paperId = 123
        paper.title = 'Test Paper'
        
        result = paper_validator.checkPapersOpenAlex([paper], processed=False)
        assert len(result) == 0
    
    def test_check_papers_filters_multiple_papers_correctly(self, paper_validator):
        paper1 = Mock()
        paper1.paperId = 'W1'
        paper1.title = 'Valid Paper'
        
        paper2 = Mock()
        paper2.paperId = None
        paper2.title = 'Invalid Paper'
        
        paper3 = Mock()
        paper3.paperId = 'W3'
        paper3.title = 'Another Valid Paper'
        
        result = paper_validator.checkPapers([paper1, paper2, paper3], processed=False)
        assert len(result) == 2