from typing import List, Dict, Optional
import logging
from collections import defaultdict
import numpy as np

from ArticleCrawler.library.models import (
    PaperData, 
    TemporalTopicData, 
    TimePeriod,
    AuthorInfo
)
from ArticleCrawler.config.temporal_config import TemporalAnalysisConfig
from ArticleCrawler.utils.time_period_calculator import TimePeriodCalculator


class TemporalAnalysisService:
    """
    Analyzes how topics evolve over time periods.
    
    This service:
    - Groups papers by time periods
    - Calculates topic distributions per period
    - Identifies trends (emerging/declining topics)
    """
    
    def __init__(
        self,
        config: TemporalAnalysisConfig,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize temporal analysis service.
        
        Args:
            config: Temporal analysis configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.period_calculator = TimePeriodCalculator(config)
    
    def analyze_evolution(
        self,
        author: AuthorInfo,
        papers: List[PaperData]
    ) -> TemporalTopicData:
        """
        Analyze topic evolution for a set of papers.
        
        Args:
            author: Author information
            papers: List of papers with topic assignments
            
        Returns:
            TemporalTopicData with distribution information
            
        Raises:
            ValueError: If insufficient papers or missing topic assignments
        """
        self._validate_papers(papers)
        
        periods = self.period_calculator.calculate_periods(papers)
        
        if not periods:
            raise ValueError("Could not create any valid time periods from papers")
        
        self.logger.info(f"Created {len(periods)} time periods for analysis")
        
        papers_by_period = self.period_calculator.assign_papers_to_periods(papers, periods)
        
        valid_periods = self._filter_periods_by_paper_count(periods, papers_by_period)
        
        if not valid_periods:
            raise ValueError(
                f"No periods have at least {self.config.min_papers_per_period} papers. "
                f"Consider reducing min_papers_per_period or time_period_years."
            )
        
        self.logger.info(f"Analyzing {len(valid_periods)} valid time periods")
        
        topic_labels = self._extract_topic_labels(papers)
        
        topic_distributions = self._calculate_topic_distributions(
            valid_periods, 
            papers_by_period, 
            topic_labels
        )
        
        paper_counts = [len(papers_by_period[p.label]) for p in valid_periods]
        
        papers_by_period_ids = {
            period.label: [p.paper_id for p in papers_by_period[period.label]]
            for period in valid_periods
        }
        
        temporal_data = TemporalTopicData(
            author_id=author.id,
            author_name=author.name,
            time_periods=valid_periods,
            topic_labels=topic_labels,
            topic_distributions=topic_distributions,
            paper_counts_per_period=paper_counts,
            total_papers=len(papers),
            papers_by_period=papers_by_period_ids
        )
        
        self.logger.info("Temporal analysis complete")
        return temporal_data
    
    def _validate_papers(self, papers: List[PaperData]):
        """Validate that papers have required information."""
        if len(papers) < self.config.min_papers_total:
            raise ValueError(
                f"Need at least {self.config.min_papers_total} papers for temporal analysis, "
                f"got {len(papers)}"
            )
        
        papers_with_topics = [p for p in papers if p.topic_label is not None]
        if not papers_with_topics:
            raise ValueError(
                "No papers have topic assignments. "
                "Run topic modeling before temporal analysis."
            )
        
        papers_with_years = [p for p in papers if p.year is not None]
        if len(papers_with_years) < self.config.min_papers_total:
            raise ValueError(
                f"Need at least {self.config.min_papers_total} papers with year information"
            )
    
    def _extract_topic_labels(self, papers: List[PaperData]) -> List[str]:
        """Extract unique topic labels from papers."""
        topics = set()
        for paper in papers:
            if paper.topic_label:
                topics.add(paper.topic_label)
        
        return sorted(list(topics))
    
    def _filter_periods_by_paper_count(
        self,
        periods: List[TimePeriod],
        papers_by_period: Dict[str, List[PaperData]]
    ) -> List[TimePeriod]:
        """Filter out periods with insufficient papers."""
        valid_periods = []
        
        for period in periods:
            paper_count = len(papers_by_period.get(period.label, []))
            if paper_count >= self.config.min_papers_per_period:
                valid_periods.append(period)
            else:
                self.logger.debug(
                    f"Skipping period {period.label} with only {paper_count} papers"
                )
        
        return valid_periods
    
    def _calculate_topic_distributions(
        self,
        periods: List[TimePeriod],
        papers_by_period: Dict[str, List[PaperData]],
        topic_labels: List[str]
    ) -> List[List[float]]:
        """
        Calculate topic distribution for each time period.
        
        Args:
            periods: List of time periods
            papers_by_period: Papers grouped by period
            topic_labels: List of all topic labels
            
        Returns:
            List of distributions, where each distribution is a list of proportions
        """
        distributions = []
        
        for period in periods:
            period_papers = papers_by_period[period.label]
            
            topic_counts = defaultdict(int)
            for paper in period_papers:
                if paper.topic_label:
                    topic_counts[paper.topic_label] += 1
            
            total = len(period_papers)
            distribution = []
            
            for topic in topic_labels:
                count = topic_counts[topic]
                proportion = count / total if total > 0 else 0.0
                distribution.append(proportion)
            
            if self.config.normalize_distributions and sum(distribution) > 0:
                total_prop = sum(distribution)
                distribution = [p / total_prop for p in distribution]
            
            distributions.append(distribution)
        
        return distributions