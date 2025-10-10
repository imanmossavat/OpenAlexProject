
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime


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


@dataclass
class TopicCluster:
    """Represents a labeled topic cluster."""
    cluster_id: int
    label: str
    paper_ids: List[str]
    representative_concepts: List[Dict[str, Any]] = field(default_factory=list)
    top_words: List[str] = field(default_factory=list)