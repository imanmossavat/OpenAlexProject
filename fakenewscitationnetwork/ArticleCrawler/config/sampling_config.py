from typing import Dict, List, Optional, Union
import numpy as np

class SamplingConfig:
    """
    Configuration for paper sampling behavior.
    
    This class handles all sampling-related settings including the number of papers
    to sample, hyperparameters for probability calculations, and venue filtering.
    """
    
    def __init__(self, 
                 num_papers: int,
                 hyper_params: Optional[Dict[str, float]] = None,
                 ignored_venues: Optional[List[str]] = None,
                 no_key_word_lambda: float = 1.0):
        """
        Initialize sampling configuration.
        
        Args:
            num_papers (int): Number of papers to sample per iteration
            hyper_params (Dict[str, float], optional): Hyperparameters for sampling probability
            ignored_venues (List[str], optional): Venues to exclude from sampling
            no_key_word_lambda (float): Lambda parameter for exponential decay in keyword-less sampling
        """
        self.num_papers = num_papers
        self.hyper_params = hyper_params or {'year': 0.1, 'centrality': 1.0}
        self.ignored_venues = ignored_venues or []
        self.no_key_word_lambda = no_key_word_lambda
        
        # Validate inputs
        if num_papers <= 0:
            raise ValueError("num_papers must be positive")
        if no_key_word_lambda < 0:
            raise ValueError("no_key_word_lambda must be non-negative")
    
    def copy(self):
        """Create a copy of this configuration."""
        return SamplingConfig(
            num_papers=self.num_papers,
            hyper_params=self.hyper_params.copy(),
            ignored_venues=self.ignored_venues.copy(),
            no_key_word_lambda=self.no_key_word_lambda
        )

class SamplingOptions(SamplingConfig):
    """Backward compatibility alias for SamplingConfig."""
    
    def __init__(self, num_papers, no_key_word_lmbda=1, hyper_params=None, ignored_venues=None):
        super().__init__(
            num_papers=num_papers,
            hyper_params=hyper_params or {'year': 0.1, 'centrality': 1},
            ignored_venues=ignored_venues,
            no_key_word_lambda=no_key_word_lmbda
        )
        
        self.no_key_word_lmbda = self.no_key_word_lambda