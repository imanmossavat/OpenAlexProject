import pytest
import networkx as nx
from unittest.mock import Mock, patch
from ArticleCrawler.graph.graph_processing import GraphProcessing


@pytest.mark.unit
class TestGraphProcessing:
    
    @pytest.fixture
    def graph_processing(self, mock_logger):
        mock_data_manager = Mock()
        mock_data_manager.graph = Mock()
        mock_data_manager.graph.DG = nx.DiGraph()
        return GraphProcessing(mock_data_manager, mock_logger)
    
    def test_initialization(self, graph_processing):
        assert graph_processing.data_manager is not None
        assert graph_processing.logger is not None
    
    @patch('ArticleCrawler.graph.graph_processing.nx.eigenvector_centrality')
    def test_calculate_centrality_updates_nodes(self, mock_eigenvector, graph_processing):
        graph_processing.data_manager.graph.DG.add_node('W1', ntype='paper')
        graph_processing.data_manager.graph.DG.add_node('W2', ntype='paper')
        graph_processing.data_manager.graph.DG.add_edge('W1', 'W2')
        
        mock_eigenvector.return_value = {'W1': 0.5, 'W2': 0.5}
        
        graph_processing.calculate_centrality()
        
        assert mock_eigenvector.call_count >= 2
    
    @patch('ArticleCrawler.graph.graph_processing.nx.eigenvector_centrality')
    def test_calculate_centrality_handles_nan_values(self, mock_eigenvector, graph_processing, mock_logger):
        graph_processing.data_manager.graph.DG.add_node('W1', ntype='paper')
        mock_eigenvector.return_value = {'W1': float('nan')}
        
        graph_processing.calculate_centrality()
        
        assert mock_logger.info.called 
