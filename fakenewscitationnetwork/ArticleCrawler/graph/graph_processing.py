import networkx as nx
import numpy as np
import pandas as pd
import logging
import os

# Set the environment variable
os.environ['PYDEVD_WARN_EVALUATION_TIMEOUT'] = '15'

class GraphProcessing:
    """
    A class responsible for calculating centrality measures for a graph in the context of a crawler program.

    This class is part of the data processing submodule within the larger crawler program. It receives a data_manager
    object that contains dataframes and a graph. 

    The graph represents a network, and this class calculates centrality
    measures for various nodes in the graph such as papers, venues, and authors.

    Depending on the nodeType, nodeId can be paperId, authorId, or venue.

    The centrality measures to be calculated may include Eigenvector Centrality.

    Example usage:
    ```
    data_manager = DataManager()
    graph_processing = GraphProcessing(data_manager)
    graph_processing.calculate_centrality()
    ```
    """

    def __init__(self, data_manager,logger=None):
        """
        Initializes the GraphProcessing class.

        Args:
        - data_manager: The data management class that holds the necessary dataframes and the graph.
        """
        self.data_manager = data_manager
        self.logger = logger or logging.getLogger(__name__)

    def calculate_centrality(self):
        """
        Calculates centrality measures for the graph.

        This method calculates centrality measures for each paper node, venue node, and author node in the graph
        stored in the data_manager. The centrality measures are stored as node attributes in the graph.

        The centrality measures to be calculated include Eigenvector Centrality for the directed graph DG and its reverse version DG.reverse().
        """
        DG = self.data_manager.graph.DG
        try:
            self.logger.info('Centralities calculation (in) starts')
            eigenvector_centrality = nx.eigenvector_centrality(DG, max_iter=1000)
            self.logger.info('Centralities (in) calculation ended') 
        
            # Update node attributes with centrality values
            for node_id, centrality_in in eigenvector_centrality.items():
                if np.isnan(centrality_in):
                    # Log information about the node with NaN centrality
                    node_info = DG.nodes[node_id]
                    node_id_msg = f'Node ID: {node_id}'
                    node_info_msg = f'Node Info: {node_info}'
                    error_message = f'NaN centrality for node {node_id}. Node details: {node_id_msg}, {node_info_msg}'
                    self.logger.info(error_message)
                else:
                    DG.nodes[node_id]['centrality (in)'] = centrality_in
        
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            self.logger.info(error_message)


        try:
            self.logger.info('Centralities calculation (out) starts')
            eigenvector_centrality_out_edge = nx.eigenvector_centrality(DG.reverse(), max_iter=1000)
            self.logger.info('Centralities (out) calculation ended') 
            
            for node_id, centrality_out in eigenvector_centrality_out_edge.items():
                if np.isnan(centrality_out):
                    # Log information about the node with NaN centrality
                    node_info = DG.nodes[node_id]
                    node_id_msg = f'Node ID: {node_id}'
                    node_info_msg = f'Node Info: {node_info}'
                    error_message = f'NaN centrality (out) for node {node_id}. Node details: {node_id_msg}, {node_info_msg}'
                    self.logger.info(error_message)
                else:
                    DG.nodes[node_id]['centrality (out)'] = centrality_out
       
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            self.logger.info(error_message)