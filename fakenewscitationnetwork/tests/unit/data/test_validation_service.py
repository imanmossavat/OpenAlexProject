import pytest
import pandas as pd
from unittest.mock import Mock
from ArticleCrawler.data.validation_service import DataValidationService


@pytest.mark.unit
class TestDataValidationService:
    
    @pytest.fixture
    def validation_service(self, mock_logger):
        return DataValidationService(mock_logger)
    
    def test_log_inconsistent_retrievals_with_no_delta(self, validation_service):
        requested_ids = ['W1', 'W2', 'W3']
        paper1 = Mock()
        paper1.paperId = 'W1'
        paper2 = Mock()
        paper2.paperId = 'W2'
        paper3 = Mock()
        paper3.paperId = 'W3'
        papers = [paper1, paper2, paper3]
        
        validation_service.log_inconsistent_retrievals(requested_ids, papers, [], [])
    
    def test_log_inconsistent_retrievals_logs_missing_papers(self, validation_service, mock_logger):
        requested_ids = ['W1', 'W2', 'W3']
        paper1 = Mock()
        paper1.paperId = 'W1'
        papers = [paper1]
        
        validation_service.log_inconsistent_retrievals(requested_ids, papers, ['W2'], [])
        assert mock_logger.warning.called
    
    def test_validate_paper_objects_filters_none_papers(self, validation_service):
        papers = [None, Mock(), None]
        valid, invalid_count = validation_service.validate_paper_objects(papers)
        assert len(valid) == 1
        assert invalid_count == 2
    
    def test_validate_paper_objects_requires_paper_id_and_title(self, validation_service):
        paper1 = Mock()
        paper1.paperId = 'W1'
        paper1.title = 'Title 1'
        
        paper2 = Mock()
        paper2.paperId = None
        paper2.title = 'Title 2'
        
        papers = [paper1, paper2]
        valid, invalid_count = validation_service.validate_paper_objects(papers)
        assert len(valid) == 1
        assert invalid_count == 1
    
    def test_check_sampler_consistency_with_correct_flags(self, validation_service):
        retrieved_ids = ['W1', 'W2']
        df = pd.DataFrame({
            'paperId': ['W1', 'W2', 'W3'],
            'selected': [True, True, False]
        })
        validation_service.check_sampler_consistency(retrieved_ids, df, True)
    
    def test_check_sampler_consistency_logs_incorrect_flags(self, validation_service, mock_logger):
        retrieved_ids = ['W1', 'W2']
        df = pd.DataFrame({
            'paperId': ['W1', 'W2', 'W3'],
            'selected': [True, False, False]
        })
        validation_service.check_sampler_consistency(retrieved_ids, df, True)
        assert mock_logger.warning.called
    
    def test_validate_processed_status_returns_true_when_all_processed(self, validation_service):
        retrieved_ids = ['W1', 'W2']
        df = pd.DataFrame({
            'paperId': ['W1', 'W2', 'W3'],
            'processed': [True, True, False]
        })
        result = validation_service.validate_processed_status(retrieved_ids, df)
        assert result == True
    
    def test_validate_processed_status_returns_false_when_not_all_processed(self, validation_service):
        retrieved_ids = ['W1', 'W2']
        df = pd.DataFrame({
            'paperId': ['W1', 'W2', 'W3'],
            'processed': [True, False, False]
        })
        result = validation_service.validate_processed_status(retrieved_ids, df)
        assert result == False 
