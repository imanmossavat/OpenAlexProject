"""
Graph Manager Module

This module provides the functionality to generate and manage a graph based on input frames. It includes functions to add edges to the graph, a dictionary of edge types, and a switch case for adding edges based on the edge type. The main class `GraphManager` is responsible for generating the graph and managing its options.

"""
BUILD_FROM_SCRATCH= True
import networkx as nx
import pandas as pd
import logging

class GraphManager:
    """
    Responsible for generating and managing the graph based on input frames.

    Args:
        graph_options (object): Options for configuring the graph generation.
        reporting_options (object): Options for reporting and analysis.

    Attributes:
        graph_options (object): Options for configuring the graph generation.
        reporting_options (object): Options for reporting and analysis.
        DG (networkx.DiGraph): Directed graph to store the generated graph.

    """
        
    def __init__(self, graph_options=None, reporting_options=None,logger=None):
        self.graph_options = graph_options
        self.reporting_options = reporting_options
        self.DG = nx.DiGraph()
        self.logger = logger or logging.getLogger(__name__)
        if self.graph_options is None:
            self.logger.info("No graph options provided.")

    def extract_graph_data(self):
        """
        Extracts the set of papers, authors, and venues from the graph.

        Returns:
            paper_ids (list): List of paper IDs.
            author_ids (list): List of author IDs.
            venues (list): List of venues.

        """
        paper_ids = [node for node, data in self.DG.nodes(data=True) if data.get('ntype') == 'paper']
        author_ids = [node for node, data in self.DG.nodes(data=True) if data.get('ntype') == 'author']
        venues = [node for node, data in self.DG.nodes(data=True) if data.get('ntype') == 'venue']

        return paper_ids, author_ids, venues
    
    def update_graph_with_new_nodes(self, frames):
        """
    Updates the graph by adding new nodes and edges from the frames.

    Args:
        frames (object): Input frames containing data for graph generation.

    Returns:
        None
    """
        if BUILD_FROM_SCRATCH:
            graph_paper_ids=[]
            graph_author_ids=[]
            graph_venues=[]
        else:
            graph_paper_ids, graph_author_ids, graph_venues = self.extract_graph_data()
            self.logger.info(f"Graph paper IDs: {len(graph_paper_ids)}, author IDs: {len(graph_author_ids)}, venues: {len(graph_venues)}")

        

        # Extract paper IDs, author IDs, and venues from the frames
        frame_paper_ids = frames.df_paper_metadata.paperId.unique()
        frame_author_ids = frames.df_paper_author.authorId.unique()
        frame_venues = frames.df_paper_metadata.venue.unique()
        self.logger.info(f"Frame paper IDs: {len(frame_paper_ids)}, author IDs: {len(frame_author_ids)}, venues: {len(frame_venues)}")

        # Identify new paper IDs, author IDs, and venues
        new_paper_ids = list(set(frame_paper_ids) - set(graph_paper_ids))
        new_author_ids = list(set(frame_author_ids) - set(graph_author_ids))
        new_venues = list(set(frame_venues) - set(graph_venues))
        self.logger.info(f"New paper IDs: {len(new_paper_ids)}, author IDs: {len(new_author_ids)}, venues: {len(new_venues)}")


        # Add new paper nodes to the graph
        self.DG.add_nodes_from(new_paper_ids, ntype='paper')
        # Add new author nodes to the graph
        if self.graph_options is not None and hasattr(self.graph_options, 'include_author_nodes') and self.graph_options.include_author_nodes:
            self.DG.add_nodes_from(new_author_ids, ntype='author')
            self.logger.info("author nodes included in graph.")
        else:
            self.logger.info("author nodes NOT included in graph.")



        # Add new author nodes to the graph and create edges from new authors to their corresponding papers
        new_author_papers = frames.df_paper_author[frames.df_paper_author.authorId.isin(new_author_ids)][['paperId', 'authorId']]
        author_paper_edges = list(zip(new_author_papers['authorId'], new_author_papers['paperId']))
        self.DG.add_edges_from(author_paper_edges, etype='author')

        # Filter out ignored venues and add new venue nodes to the graph
        new_venues_filtered = [venue for venue in new_venues if venue not in self.graph_options.ignored_venues]
        self.DG.add_nodes_from(new_venues_filtered, ntype='venue')

        # Create edges from new venues to their corresponding papers
        new_venue_papers = frames.df_paper_metadata[frames.df_paper_metadata.venue.isin(new_venues_filtered)][['venue', 'paperId']]
        venue_paper_edges = list(zip(new_venue_papers['venue'], new_venue_papers['paperId']))
        self.DG.add_edges_from(venue_paper_edges, etype='venue')

        # Create edges for new papers based on citation links
        new_paper_citations = frames.df_paper_citations[frames.df_paper_citations.paperId.isin(new_paper_ids)][['paperId', 'citedPaperId']]
        citation_edges = list(zip(new_paper_citations['paperId'], new_paper_citations['citedPaperId']))
        self.DG.add_edges_from(citation_edges, etype='citation')

        # Create edges for new papers based on reference links
        new_paper_references = frames.df_paper_references[frames.df_paper_references.paperId.isin(new_paper_ids)][['referencePaperId', 'paperId']]
        reference_edges = list(zip(new_paper_references['referencePaperId'], new_paper_references['paperId']))
        self.DG.add_edges_from(reference_edges, etype='reference')

        return None
    
    def get_graph_info(self):
        num_nodes = len(self.DG.nodes())
        num_edges = len(self.DG.edges())
        return num_nodes, num_edges
    
    def get_paper_centralities(self, paperIds):
        """
        extract centralities
        """
        paper_id_set = set(paperIds)

        centralities = [(node, data.get('centrality (in)'), data.get('centrality (out)')) 
                        for node, data in self.DG.nodes(data=True) 
                        if data.get('ntype') == 'paper' and node in paper_id_set]

        if not centralities:
            return pd.DataFrame()  # Return an empty DataFrame if no paper in paperIds found

        
        return pd.DataFrame(centralities, columns=['paperId', 'centrality (in)', 'centrality (out)']) 
    
    def get_all_paper_centralities(self,data_manager):
        return self.get_paper_centralities(data_manager.frames.df_paper_metadata.paperId)

    def get_centrality_statistics(self,data_manager):
        centralities_df = self.get_all_paper_centralities(data_manager)
        centrality_stats = centralities_df[['centrality (in)', 'centrality (out)']].describe()
        return centrality_stats
    
    def get_author_centralities(self):
        """
        extract centralities
        """

        centralities = [(node, data.get('centrality (in)'), data.get('centrality (out)')) 
                        for node, data in self.DG.nodes(data=True) 
                        if data.get('ntype') == 'author' ]

        if not centralities:
            return pd.DataFrame()  # Return an empty DataFrame if no paper in paperIds found

        
        return pd.DataFrame(centralities, columns=['paperId', 'centrality (in)', 'centrality (out)']) 

    def get_venue_centralities(self):
        """
        extract centralities
        """

        centralities = [(node, data.get('centrality (in)'), data.get('centrality (out)')) 
                        for node, data in self.DG.nodes(data=True) 
                        if data.get('ntype') == 'venue' ]

        if not centralities:
            return pd.DataFrame()  # Return an empty DataFrame if no paper in paperIds found

        
        return pd.DataFrame(centralities, columns=['paperId', 'centrality (in)', 'centrality (out)']) 

