 
import pytest
import pandas as pd
from unittest.mock import Mock


@pytest.mark.integration
class TestDataToGraphFlow:
    
    def test_update_graph_from_frames(
        self,
        integration_frame_manager,
        sample_paper_metadata_df,
        sample_graph_config,
        mock_logger
    ):
        from ArticleCrawler.graph import GraphManager
        
        integration_frame_manager.df_paper_metadata = sample_paper_metadata_df
        integration_frame_manager.df_paper_citations = pd.DataFrame({
            'paperId': ['W2134567890'],
            'citedPaperId': ['W9876543210']
        })
        integration_frame_manager.df_paper_references = pd.DataFrame({
            'paperId': ['W9876543210'],
            'referencePaperId': ['W2134567890']
        })
        integration_frame_manager.df_paper_author = pd.DataFrame({
            'paperId': ['W2134567890'],
            'authorId': ['A1']
        })
        
        graph_manager = GraphManager(graph_options=sample_graph_config, logger=mock_logger)
        graph_manager.update_graph_with_new_nodes(integration_frame_manager)
        
        num_nodes, num_edges = graph_manager.get_graph_info()
        assert num_nodes > 0