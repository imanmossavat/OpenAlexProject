 
import pytest
import networkx as nx
import pandas as pd
from unittest.mock import Mock, patch
from ArticleCrawler.graph.graph_manager import GraphManager


@pytest.mark.unit
class TestGraphManager:
    
    @pytest.fixture
    def graph_manager(self, sample_graph_config, mock_logger):
        return GraphManager(graph_options=sample_graph_config, logger=mock_logger)
    
    def test_initialization_creates_empty_graph(self, graph_manager):
        assert isinstance(graph_manager.DG, nx.DiGraph)
        assert len(graph_manager.DG.nodes()) == 0
    
    def test_extract_graph_data_returns_empty_lists_for_empty_graph(self, graph_manager):
        paper_ids, author_ids, venues = graph_manager.extract_graph_data()
        assert paper_ids == []
        assert author_ids == []
        assert venues == []
    
    def test_update_graph_with_new_nodes_adds_paper_nodes(self, graph_manager, mock_frame_manager):
        mock_frame_manager.df_paper_metadata = pd.DataFrame({
            'paperId': ['W1', 'W2'],
            'venue': ['Venue A', 'Venue B']
        })
        mock_frame_manager.df_paper_author = pd.DataFrame({
            'paperId': ['W1'],
            'authorId': ['A1']
        })
        mock_frame_manager.df_paper_citations = pd.DataFrame({
            'paperId': ['W1'],
            'citedPaperId': ['W2']
        })
        mock_frame_manager.df_paper_references = pd.DataFrame({
            'paperId': ['W2'],
            'referencePaperId': ['W1']
        })
        
        graph_manager.update_graph_with_new_nodes(mock_frame_manager)
        assert len(graph_manager.DG.nodes()) > 0
    
    def test_get_graph_info_returns_node_and_edge_counts(self, graph_manager):
        graph_manager.DG.add_node('W1', ntype='paper')
        graph_manager.DG.add_node('W2', ntype='paper')
        graph_manager.DG.add_edge('W1', 'W2')
        
        num_nodes, num_edges = graph_manager.get_graph_info()
        assert num_nodes == 2
        assert num_edges == 1
    
    def test_get_paper_centralities_returns_empty_for_no_papers(self, graph_manager):
        result = graph_manager.get_paper_centralities(['W1', 'W2'])
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    def test_get_paper_centralities_returns_centrality_data(self, graph_manager):
        graph_manager.DG.add_node('W1', ntype='paper')
        graph_manager.DG.nodes['W1']['centrality (in)'] = 0.5
        graph_manager.DG.nodes['W1']['centrality (out)'] = 0.3
        
        result = graph_manager.get_paper_centralities(['W1'])
        assert len(result) == 1
        assert 'centrality (in)' in result.columns