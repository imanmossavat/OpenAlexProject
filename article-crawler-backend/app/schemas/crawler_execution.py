"""
Pydantic schemas for crawler execution and results.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class StartCrawlerRequest(BaseModel):
    """Request to start the crawler after all configuration is complete."""
    use_case: str = Field(default="crawler_wizard", description="Use case identifier")
    library_path: Optional[str] = Field(default=None, description="Absolute path to the selected library")
    library_name: Optional[str] = Field(default=None, description="Optional library name for display/traceability")
    
    class Config:
        json_schema_extra = {
            "example": {
                "use_case": "crawler_wizard"
            }
        }


class CrawlerStatus(BaseModel):
    """Status information for a running or completed crawler job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: running, completed, failed")
    current_iteration: int = Field(default=0, description="Current iteration number")
    max_iterations: int = Field(..., description="Maximum iterations configured")
    papers_collected: int = Field(default=0, description="Total papers collected so far")
    started_at: datetime = Field(..., description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123456",
                "status": "running",
                "current_iteration": 2,
                "max_iterations": 5,
                "papers_collected": 150,
                "started_at": "2025-10-29T10:30:00",
                "completed_at": None,
                "error_message": None
            }
        }


class StartCrawlerResponse(BaseModel):
    """Response after starting the crawler."""
    job_id: str = Field(..., description="Unique job identifier for tracking")
    status: str = Field(..., description="Initial status: running")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123456",
                "status": "running",
                "message": "Crawler started successfully"
            }
        }


class NetworkOverview(BaseModel):
    """Overview statistics of the citation network."""
    total_nodes: int = Field(..., description="Total number of nodes (papers + authors if enabled)")
    total_edges: int = Field(..., description="Total number of edges (citations)")
    paper_nodes: int = Field(..., description="Number of paper nodes")
    author_nodes: int = Field(0, description="Number of author nodes (if enabled)")
    total_papers: int = Field(..., description="Total papers collected")
    total_iterations: int = Field(..., description="Number of iterations completed")
    total_topics: int = Field(..., description="Number of topics discovered")
    retracted_papers: int = Field(0, description="Number of retracted papers detected")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_nodes": 500,
                "total_edges": 1500,
                "paper_nodes": 500,
                "author_nodes": 0,
                "total_papers": 500,
                "total_iterations": 5,
                "total_topics": 20,
                "retracted_papers": 3
            }
        }


class TemporalDistribution(BaseModel):
    """Distribution of papers by publication year."""
    year: int = Field(..., description="Publication year")
    paper_count: int = Field(..., description="Number of papers published in this year")
    
    class Config:
        json_schema_extra = {
            "example": {
                "year": 2020,
                "paper_count": 45
            }
        }


class PaperMetadata(BaseModel):
    """Paper metadata with centrality score."""
    paper_id: str = Field(..., description="Paper ID")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    year: Optional[int] = Field(None, description="Publication year")
    venue: Optional[str] = Field(None, description="Publication venue")
    doi: Optional[str] = Field(None, description="DOI")
    citation_count: Optional[int] = Field(None, description="Total citations")
    centrality_score: float = Field(..., description="Eigenvector centrality score")
    is_seed: bool = Field(False, description="Whether this was a seed paper")
    is_retracted: bool = Field(False, description="Whether paper is retracted")
    url: Optional[str] = Field(None, description="URL to paper")
    
    class Config:
        json_schema_extra = {
            "example": {
                "paper_id": "W2741809807",
                "title": "Deep Learning in Healthcare",
                "authors": ["John Doe", "Jane Smith"],
                "year": 2020,
                "venue": "Nature Medicine",
                "doi": "10.1038/example",
                "citation_count": 150,
            "centrality_score": 0.85,
            "is_seed": True,
            "is_retracted": False,
            "url": "https://openalex.org/W2741809807"
        }
        }


class TopicOverview(BaseModel):
    """Overview of a discovered topic."""
    topic_id: int = Field(..., description="Topic ID")
    topic_label: str = Field(..., description="Topic label/name")
    paper_count: int = Field(..., description="Number of papers in this topic")
    top_words: List[str] = Field(default_factory=list, description="Top words for this topic")
    paper_ids: List[str] = Field(default_factory=list, description="List of paper IDs in this topic")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic_id": 5,
                "topic_label": "Machine Learning in Medicine",
                "paper_count": 45,
                "top_words": ["learning", "neural", "network", "training", "model"],
                "paper_ids": ["W123", "W456", "W789"]
            }
        }


class AuthorInfluence(BaseModel):
    """Author with influence metrics."""
    author_id: str = Field(..., description="Author ID")
    author_name: str = Field(..., description="Author name")
    paper_count: int = Field(..., description="Number of papers by this author in network")
    centrality_score: float = Field(..., description="Centrality score (author node or average of papers)")
    total_citations: int = Field(0, description="Total citations across their papers")
    
    class Config:
        json_schema_extra = {
            "example": {
                "author_id": "A123456",
                "author_name": "John Doe",
                "paper_count": 8,
                "centrality_score": 0.75,
                "total_citations": 450
            }
        }


class CrawlerResults(BaseModel):
    """Complete results from a crawler run."""
    job_id: str = Field(..., description="Job identifier")
    network_overview: NetworkOverview = Field(..., description="Network statistics")
    temporal_distribution: List[TemporalDistribution] = Field(
        default_factory=list,
        description="Papers by year"
    )
    top_papers: List[PaperMetadata] = Field(
        default_factory=list,
        description="Top papers by centrality"
    )
    topics: List[TopicOverview] = Field(
        default_factory=list,
        description="Discovered topics"
    )
    top_authors: List[AuthorInfluence] = Field(
        default_factory=list,
        description="Most influential authors"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123456",
                "network_overview": {
                    "total_nodes": 500,
                    "total_edges": 1500,
                    "paper_nodes": 500,
                    "author_nodes": 0,
                    "total_papers": 500,
                    "total_iterations": 5,
                    "total_topics": 20,
                    "retracted_papers": 3
                },
                "temporal_distribution": [
                    {"year": 2020, "paper_count": 45}
                ],
                "top_papers": [],
                "topics": [],
                "top_authors": []
            }
        }


class TopicPapersResponse(BaseModel):
    """Papers belonging to a specific topic."""
    topic_id: int = Field(..., description="Topic ID")
    topic_label: str = Field(..., description="Topic label")
    papers: List[PaperMetadata] = Field(..., description="Papers in this topic")
    total_count: int = Field(..., description="Total papers in topic")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic_id": 5,
                "topic_label": "Machine Learning in Medicine",
                "papers": [],
                "total_count": 45
            }
        }
