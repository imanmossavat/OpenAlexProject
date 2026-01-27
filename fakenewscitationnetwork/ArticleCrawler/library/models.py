
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from ..normalization import normalize_venue


@dataclass
class LibraryConfig:
    """Configuration for a paper library."""
    name: str
    base_path: Path
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    api_provider: str = 'openalex'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'base_path': str(self.base_path),
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'api_provider': self.api_provider
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LibraryConfig':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            base_path=Path(data['base_path']),
            description=data.get('description'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            api_provider=data.get('api_provider', 'openalex')
        )


@dataclass
class PaperData:
    """Paper data with OpenAlex metadata."""
    paper_id: str
    title: str
    authors: List[Dict[str, str]]
    year: Optional[int] = None
    venue: Optional[str] = None
    venue_raw: Optional[str] = None
    venue_id: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    
    concepts: List[Dict[str, Any]] = field(default_factory=list)
    topics: List[Dict[str, Any]] = field(default_factory=list)
    subfields: List[Dict[str, Any]] = field(default_factory=list)
    fields: List[Dict[str, Any]] = field(default_factory=list)
    domains: List[Dict[str, Any]] = field(default_factory=list)
    
    assigned_topic: Optional[int] = None
    topic_label: Optional[str] = None

    def __post_init__(self) -> None:
        if self.venue_raw is None:
            self.venue_raw = self.venue
        normalized = normalize_venue(self.venue_raw)
        if normalized:
            self.venue = normalized
        elif self.venue_raw:
            self.venue = self.venue_raw.strip()


@dataclass
class TopicCluster:
    """Represents a labeled topic cluster."""
    cluster_id: int
    label: str
    paper_ids: List[str]
    representative_concepts: List[Dict[str, Any]] = field(default_factory=list)
    top_words: List[str] = field(default_factory=list)

# Add these new dataclasses to the existing models.py file

@dataclass
class AuthorInfo:
    """Information about an author from OpenAlex."""
    id: str  # A1234567890
    name: str
    works_count: int
    cited_by_count: int
    institutions: List[str] = field(default_factory=list)
    orcid: Optional[str] = None
    
    def __str__(self):
        """String representation for display."""
        inst_str = f" - {', '.join(self.institutions[:2])}" if self.institutions else ""
        return f"{self.name}{inst_str} ({self.works_count} papers, {self.cited_by_count:,} citations)"


@dataclass
class TimePeriod:
    """Represents a time period for temporal analysis."""
    start_year: int
    end_year: int
    label: str = ""
    
    def __post_init__(self):
        if not self.label:
            if self.start_year == self.end_year:
                self.label = str(self.start_year)
            else:
                self.label = f"{self.start_year}-{self.end_year}"
    
    def contains_year(self, year: int) -> bool:
        """Check if a year falls within this period."""
        return self.start_year <= year <= self.end_year
    
    def __str__(self):
        return self.label


@dataclass
class TemporalTopicData:
    """Topic distribution data over time periods."""
    author_id: str
    author_name: str
    time_periods: List[TimePeriod]
    topic_labels: List[str]
    
    topic_distributions: List[List[float]]
    
    paper_counts_per_period: List[int]
    total_papers: int
    
    papers_by_period: Dict[str, List[str]] = field(default_factory=dict)
    
    def get_topic_trend(self, topic_label: str) -> List[float]:
        """Get the trend for a specific topic across time periods."""
        try:
            topic_idx = self.topic_labels.index(topic_label)
            return [period_dist[topic_idx] for period_dist in self.topic_distributions]
        except ValueError:
            return []
    
    def get_period_distribution(self, period_idx: int) -> Dict[str, float]:
        """Get topic distribution for a specific period as a dictionary."""
        if 0 <= period_idx < len(self.topic_distributions):
            return dict(zip(self.topic_labels, self.topic_distributions[period_idx]))
        return {}
    
    def get_emerging_topics(self, threshold: float = 0.5) -> List[str]:
        """
        Identify topics that have grown significantly.
        
        Args:
            threshold: Minimum growth factor to be considered emerging
        
        Returns:
            List of topic labels that are emerging
        """
        emerging = []
        for i, topic in enumerate(self.topic_labels):
            if len(self.topic_distributions) < 2:
                continue
            
            first_val = self.topic_distributions[0][i]
            last_val = self.topic_distributions[-1][i]
            
            if first_val > 0:
                growth = (last_val - first_val) / first_val
                if growth >= threshold:
                    emerging.append(topic)
            elif last_val > 0.1:
                emerging.append(topic)
        
        return emerging
    
    def get_declining_topics(self, threshold: float = 0.5) -> List[str]:
        """
        Identify topics that have declined significantly.
        
        Args:
            threshold: Minimum decline factor to be considered declining
        
        Returns:
            List of topic labels that are declining
        """
        declining = []
        for i, topic in enumerate(self.topic_labels):
            if len(self.topic_distributions) < 2:
                continue
            
            first_val = self.topic_distributions[0][i]
            last_val = self.topic_distributions[-1][i]
            
            if first_val > 0:
                decline = (first_val - last_val) / first_val
                if decline >= threshold:
                    declining.append(topic)
        
        return declining


@dataclass
class AuthorTopicEvolutionResult:
    """Complete result of author topic evolution analysis."""
    author: AuthorInfo
    temporal_data: TemporalTopicData
    visualization_path: Path
    library_path: Optional[Path] = None
    is_temporary: bool = True
    
    model_type: str = "NMF"
    num_topics: int = 5
    time_period_years: int = 3
    
    def summary(self) -> str:
        """Generate a text summary of the analysis."""
        lines = [
            f"Author: {self.author.name}",
            f"Total Papers Analyzed: {self.temporal_data.total_papers}",
            f"Time Span: {self.temporal_data.time_periods[0]} to {self.temporal_data.time_periods[-1]}",
            f"Number of Topics: {len(self.temporal_data.topic_labels)}",
            f"Model Used: {self.model_type}",
            "",
            "Time Periods:",
        ]
        
        for i, period in enumerate(self.temporal_data.time_periods):
            count = self.temporal_data.paper_counts_per_period[i]
            lines.append(f"  - {period}: {count} papers")
        
        emerging = self.temporal_data.get_emerging_topics()
        if emerging:
            lines.append("")
            lines.append("Emerging Topics:")
            for topic in emerging:
                lines.append(f"  - {topic}")
        
        declining = self.temporal_data.get_declining_topics()
        if declining:
            lines.append("")
            lines.append("Declining Topics:")
            for topic in declining:
                lines.append(f"  - {topic}")
        
        lines.append("")
        if self.is_temporary:
            lines.append(f"Visualization: {self.visualization_path} (temporary)")
        else:
            lines.append(f"Library: {self.library_path}")
            lines.append(f"Visualization: {self.visualization_path}")
        
        return "\n".join(lines)
