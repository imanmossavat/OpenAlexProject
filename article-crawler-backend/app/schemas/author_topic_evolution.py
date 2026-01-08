from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class AuthorCandidate(BaseModel):
    id: str
    name: str
    works_count: int = 0
    cited_by_count: int = 0
    institutions: List[str] = Field(default_factory=list)
    orcid: Optional[str] = None


class SearchAuthorsRequest(BaseModel):
    query: str = Field(..., description="Author name to search")
    limit: int = Field(default=10, ge=1, le=20)
    api_provider: str = Field(default="openalex")


class SearchAuthorsResponse(BaseModel):
    query: str
    total_results: int
    authors: List[AuthorCandidate] = Field(default_factory=list)


class StartAuthorEvolutionRequest(BaseModel):
    author_id: str = Field(..., description="Selected author ID (e.g., OpenAlex A123...)")
    author_name: Optional[str] = Field(default=None, description="Human-readable author name for search disambiguation")
    model_type: str = Field(default="NMF", description="NMF or LDA")
    num_topics: int = Field(default=5, ge=2, le=50)
    time_period_years: int = Field(default=3, ge=1, le=10)
    max_papers: Optional[int] = Field(default=None, ge=1)
    save_library: bool = Field(default=False)
    library_path: Optional[str] = Field(default=None, description="Folder where to save the library (if save_library=true)")
    output_path: Optional[str] = Field(default=None, description="Optional custom output path for visualization image")
    api_provider: str = Field(default="openalex")

    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        v_up = v.upper()
        if v_up not in {"NMF", "LDA"}:
            raise ValueError("model_type must be 'NMF' or 'LDA'")
        return v_up


class PeriodCount(BaseModel):
    period_label: str
    paper_count: int


class StartAuthorEvolutionResponse(BaseModel):
    author: AuthorCandidate
    model_type: str
    num_topics: int
    time_period_years: int
    total_papers: int
    periods: List[PeriodCount] = Field(default_factory=list)
    topics_identified: List[str] = Field(default_factory=list)
    emerging_topics: List[str] = Field(default_factory=list)
    declining_topics: List[str] = Field(default_factory=list)
    is_temporary: bool
    visualization_path: str
    library_path: Optional[str] = None
    period_labels: List[str] = Field(default_factory=list, description="Labels for each time period")
    topic_labels: List[str] = Field(default_factory=list, description="Labels for each topic")
    topic_proportions: List[List[float]] = Field(
        default_factory=list,
        description="Matrix of topic proportions per period (rows=periods, cols=topics)"
    )
