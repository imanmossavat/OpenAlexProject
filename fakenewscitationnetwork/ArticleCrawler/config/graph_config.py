from typing import List, Optional

class GraphConfig:
    """
    Configuration for graph construction and processing.
    
    This class handles all graph-related settings including node types,
    venue filtering, and centrality calculation options.
    """
    
    def __init__(self,
                 ignored_venues: Optional[List[str]] = None,
                 include_author_nodes: bool = False,
                 include_venue_nodes: bool = True,
                 max_centrality_iterations: int = 1000):
        """
        Initialize graph configuration.
        
        Args:
            ignored_venues (List[str], optional): Venues to exclude from graph
            include_author_nodes (bool): Whether to include author nodes in graph
            include_venue_nodes (bool): Whether to include venue nodes in graph  
            max_centrality_iterations (int): Maximum iterations for centrality calculations
        """
        self.ignored_venues = ignored_venues or []
        self.include_author_nodes = include_author_nodes
        self.include_venue_nodes = include_venue_nodes
        self.max_centrality_iterations = max_centrality_iterations
        
        if max_centrality_iterations <= 0:
            raise ValueError("max_centrality_iterations must be positive")
    
    def copy(self):
        """Create a copy of this configuration."""
        return GraphConfig(
            ignored_venues=self.ignored_venues.copy(),
            include_author_nodes=self.include_author_nodes,
            include_venue_nodes=self.include_venue_nodes,
            max_centrality_iterations=self.max_centrality_iterations
        )

class GraphOptions(GraphConfig):
    """Backward compatibility alias for GraphConfig."""
    
    def __init__(self, ignored_venue=None, include_author_nodes=False):
        # Map old parameter names to new ones
        super().__init__(
            ignored_venues=ignored_venue,
            include_author_nodes=include_author_nodes
        )
        
        # Keep old attribute name for compatibility
        self.ignored_venue = self.ignored_venues