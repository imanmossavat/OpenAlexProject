import pytest
from unittest.mock import Mock, patch


@pytest.mark.integration
class TestAPIToDataFlow:
    
    def test_retrieve_papers_updates_frames(
        self,
        integration_data_coordinator,
        sample_papers_list,
        mock_api_with_sample_data
    ):
        integration_data_coordinator.retrieval.api = mock_api_with_sample_data
        
        paper_ids = ['W2134567890', 'W9876543210']
        integration_data_coordinator.retrieve_and_process_papers(paper_ids)
        
        integration_data_coordinator.frames.process_data.assert_called_once()
    
    def test_failed_papers_tracked_correctly(
        self,
        integration_data_coordinator,
        mock_api_provider
    ):
        mock_api_provider.get_papers.return_value = []
        mock_api_provider.failed_paper_ids = ['W9999999999']
        integration_data_coordinator.retrieval.api = mock_api_provider
        
        integration_data_coordinator.retrieve_and_process_papers(['W9999999999'])
        
        failed = integration_data_coordinator.retrieval.get_failed_papers()
        assert 'W9999999999' in failed