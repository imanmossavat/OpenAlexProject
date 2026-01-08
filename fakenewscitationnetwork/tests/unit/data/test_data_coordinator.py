 
import pytest
from unittest.mock import Mock, patch
from ArticleCrawler.data.data_coordinator import DataCoordinator


@pytest.mark.unit
class TestDataCoordinator:
    
    @pytest.fixture
    def data_coordinator(
        self,
        mock_retrieval_service,
        mock_validation_service,
        mock_frame_manager,
        mock_graph_manager,
        mock_retraction_manager,
        mock_logger
    ):
        graph_processing = Mock()
        return DataCoordinator(
            retrieval_service=mock_retrieval_service,
            validation_service=mock_validation_service,
            frame_manager=mock_frame_manager,
            retraction_manager=mock_retraction_manager,
            graph_manager=mock_graph_manager,
            graph_processing=graph_processing,
            crawl_initial_condition=None,
            logger=mock_logger
        )
    
    def test_retrieve_and_process_papers_with_empty_list(self, data_coordinator):
        data_coordinator.retrieve_and_process_papers([])
        assert data_coordinator.retrieval.retrieve_papers.call_count == 0
    
    def test_retrieve_and_process_papers_calls_retrieval_service(self, data_coordinator):
        paper_ids = ['W1', 'W2']
        data_coordinator.retrieval.retrieve_papers.return_value = [Mock(), Mock()]
        data_coordinator.retrieve_and_process_papers(paper_ids)
        data_coordinator.retrieval.retrieve_papers.assert_called_once()
    
    def test_retrieve_and_process_papers_updates_failed_papers(self, data_coordinator):
        paper_ids = ['W1', 'W2']
        data_coordinator.retrieval.retrieve_papers.return_value = []
        data_coordinator.retrieval.get_failed_papers.return_value = ['W2']
        data_coordinator.retrieve_and_process_papers(paper_ids)
        data_coordinator.frames.update_failed_papers.assert_called_once()
    
    def test_retrieve_and_process_papers_processes_data(self, data_coordinator):
        paper_ids = ['W1', 'W2']
        papers = [Mock(), Mock()]
        data_coordinator.retrieval.retrieve_papers.return_value = papers
        data_coordinator.retrieve_and_process_papers(paper_ids)
        data_coordinator.frames.process_data.assert_called_once_with(papers)
    
    def test_add_user_papers_retrieves_and_processes(self, data_coordinator):
        paper_ids = ['W1', 'W2']
        with patch.object(data_coordinator, 'retrieve_and_process_papers') as mock_retrieve:
            data_coordinator.add_user_papers(paper_ids)
            mock_retrieve.assert_called_once_with(paper_ids)
    
    def test_update_graph_calls_graph_manager(self, data_coordinator):
        data_coordinator.update_graph()
        data_coordinator.graph.update_graph_with_new_nodes.assert_called_once()
    
    def test_update_graph_and_calculate_centrality(self, data_coordinator):
        data_coordinator.update_graph_and_calculate_centrality()
        data_coordinator.graph.update_graph_with_new_nodes.assert_called_once()
        data_coordinator.graph_processing.calculate_centrality.assert_called_once()
    
    def test_extract_text_returns_abstracts_and_titles(self, data_coordinator, sample_paper_metadata_df, sample_abstracts_df):
        data_coordinator.frames.df_paper_metadata = sample_paper_metadata_df
        data_coordinator.frames.df_abstract = sample_abstracts_df
        abstracts, titles = data_coordinator.extract_text()
        assert len(abstracts) > 0
        assert len(titles) > 0