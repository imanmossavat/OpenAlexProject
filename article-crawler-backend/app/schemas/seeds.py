from pydantic import BaseModel, Field
from typing import List, Optional


class MatchedSeed(BaseModel):
    """A successfully matched seed paper."""
    paper_id: str
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    matched: bool = True
    confidence: float = 1.0
    match_method: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    cited_by_count: Optional[int] = None
    references_count: Optional[int] = None
    institutions: Optional[List[str]] = None


class UnmatchedSeed(BaseModel):
    """A seed paper that could not be matched."""
    input_id: str
    matched: bool = False
    error: str


class SeedMatchResult(BaseModel):
    """Result of matching seed papers."""
    matched_seeds: List[MatchedSeed]
    unmatched_seeds: List[UnmatchedSeed]
    total_matched: int
    total_unmatched: int


class PaperIDsRequest(BaseModel):
    """Request to match paper IDs."""
    paper_ids: List[str] = Field(
        ..., 
        description="List of paper IDs (OpenAlex IDs like W123456789, DOIs, or Semantic Scholar IDs)",
        min_length=1
    )
    api_provider: str = Field(
        default="openalex", 
        description="API provider to use for matching (openalex or semantic_scholar)"
    )


class PaperIDsResponse(BaseModel):
    """Response after matching paper IDs."""
    result: SeedMatchResult
