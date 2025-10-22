from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class TemporalAnalysisConfig:
    """Configuration for temporal topic analysis."""
    
    time_period_years: int = 3
    """Number of years per time period"""
    
    period_strategy: Literal["fixed", "adaptive", "custom"] = "fixed"
    """
    Strategy for creating time periods:
    - fixed: Equal-sized periods (e.g., 3 years each)
    - adaptive: Adjust period size to ensure minimum papers per period
    - custom: User-defined periods
    """
    
    min_papers_per_period: int = 2
    """Minimum number of papers required for a period to be included"""
    
    min_papers_total: int = 5
    """Minimum total papers required to perform temporal analysis"""
    
    include_partial_periods: bool = True
    """Whether to include incomplete periods at the start/end"""
    
    normalize_distributions: bool = True
    """Whether to normalize topic distributions to sum to 1.0 per period"""
    
    emerging_threshold: float = 0.5
    """Minimum growth factor for a topic to be considered 'emerging' (0.5 = 50% growth)"""
    
    declining_threshold: float = 0.5
    """Minimum decline factor for a topic to be considered 'declining' (0.5 = 50% decline)"""
    
    custom_periods: Optional[list] = None
    """List of (start_year, end_year) tuples for custom periods"""
    
    def validate(self):
        """Validate configuration parameters."""
        if self.time_period_years < 1:
            raise ValueError("time_period_years must be at least 1")
        
        if self.min_papers_per_period < 1:
            raise ValueError("min_papers_per_period must be at least 1")
        
        if self.min_papers_total < 1:
            raise ValueError("min_papers_total must be at least 1")
        
        if not 0 <= self.emerging_threshold <= 5:
            raise ValueError("emerging_threshold must be between 0 and 5")
        
        if not 0 <= self.declining_threshold <= 5:
            raise ValueError("declining_threshold must be between 0 and 5")
        
        if self.period_strategy == "custom" and not self.custom_periods:
            raise ValueError("custom_periods must be provided when using 'custom' strategy")