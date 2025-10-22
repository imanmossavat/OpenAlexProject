from typing import List, Tuple, Optional
from ArticleCrawler.library.models import TimePeriod, PaperData
from ArticleCrawler.config.temporal_config import TemporalAnalysisConfig


class TimePeriodCalculator:
    """
    Calculates time periods for temporal analysis.
    
    Supports multiple strategies:
    - Fixed intervals (e.g., 3-year periods)
    - Adaptive intervals (adjust to ensure minimum papers per period)
    - Custom user-defined periods
    """
    
    def __init__(self, config: TemporalAnalysisConfig):
        """
        Initialize calculator with configuration.
        
        Args:
            config: Temporal analysis configuration
        """
        self.config = config
    
    def calculate_periods(self, papers: List[PaperData]) -> List[TimePeriod]:
        """
        Calculate time periods based on paper years and configuration strategy.
        
        Args:
            papers: List of papers with year information
            
        Returns:
            List of TimePeriod objects
            
        Raises:
            ValueError: If papers lack year information or are insufficient
        """
        years = self._extract_years(papers)
        
        if not years:
            raise ValueError("No papers with valid year information")
        
        if self.config.period_strategy == "fixed":
            return self._calculate_fixed_periods(years)
        elif self.config.period_strategy == "adaptive":
            return self._calculate_adaptive_periods(papers, years)
        elif self.config.period_strategy == "custom":
            return self._calculate_custom_periods()
        else:
            raise ValueError(f"Unknown period strategy: {self.config.period_strategy}")
    
    def _extract_years(self, papers: List[PaperData]) -> List[int]:
        """Extract valid years from papers."""
        years = [p.year for p in papers if p.year is not None and p.year > 0]
        return sorted(years)
    
    def _calculate_fixed_periods(self, years: List[int]) -> List[TimePeriod]:
        """
        Calculate fixed-size time periods.
        
        Args:
            years: Sorted list of years
            
        Returns:
            List of TimePeriod objects with equal intervals
        """
        if not years:
            return []
        
        min_year = min(years)
        max_year = max(years)
        
        periods = []
        current_start = min_year
        
        while current_start <= max_year:
            current_end = current_start + self.config.time_period_years - 1
            
            if current_end > max_year:
                if self.config.include_partial_periods:
                    current_end = max_year
                else:
                    break
            
            period = TimePeriod(start_year=current_start, end_year=current_end)
            periods.append(period)
            
            current_start = current_end + 1
        
        return periods
    
    def _calculate_adaptive_periods(
        self, 
        papers: List[PaperData], 
        years: List[int]
    ) -> List[TimePeriod]:
        """
        Calculate adaptive periods ensuring minimum papers per period.
        
        Args:
            papers: List of papers
            years: Sorted list of years
            
        Returns:
            List of TimePeriod objects with adaptive sizes
        """
        if not years:
            return []
        
        min_year = min(years)
        max_year = max(years)
        
        periods = []
        current_start = min_year
        
        while current_start <= max_year:
            current_end = current_start + self.config.time_period_years - 1
            
            papers_in_period = sum(
                1 for p in papers 
                if p.year and current_start <= p.year <= current_end
            )
            
            while (papers_in_period < self.config.min_papers_per_period and 
                   current_end < max_year):
                current_end += 1
                papers_in_period = sum(
                    1 for p in papers 
                    if p.year and current_start <= p.year <= current_end
                )
            
            if papers_in_period >= self.config.min_papers_per_period:
                period = TimePeriod(start_year=current_start, end_year=current_end)
                periods.append(period)
            
            current_start = current_end + 1
        
        return periods
    
    def _calculate_custom_periods(self) -> List[TimePeriod]:
        """
        Calculate custom user-defined periods.
        
        Returns:
            List of TimePeriod objects from custom configuration
        """
        if not self.config.custom_periods:
            raise ValueError("No custom periods defined in configuration")
        
        periods = []
        for start, end in self.config.custom_periods:
            periods.append(TimePeriod(start_year=start, end_year=end))
        
        return sorted(periods, key=lambda p: p.start_year)
    
    def assign_papers_to_periods(
        self, 
        papers: List[PaperData], 
        periods: List[TimePeriod]
    ) -> dict[str, List[PaperData]]:
        """
        Assign papers to their corresponding time periods.
        
        Args:
            papers: List of papers
            periods: List of time periods
            
        Returns:
            Dictionary mapping period labels to lists of papers
        """
        assignments = {period.label: [] for period in periods}
        
        for paper in papers:
            if paper.year is None:
                continue
            
            for period in periods:
                if period.contains_year(paper.year):
                    assignments[period.label].append(paper)
                    break
        
        return assignments