from typing import Dict, List, Optional, Literal

from pydantic import BaseModel, Field

from app.schemas.staging import ColumnFilterOption


class PaperDetail(BaseModel):
    """Full metadata for a paper fetched from a provider like OpenAlex."""

    paper_id: str = Field(..., description="Canonical paper identifier (e.g., OpenAlex W-ID)")
    title: str = Field(..., description="Paper title")
    abstract: Optional[str] = Field(None, description="Abstract text if available")
    authors: List[str] = Field(default_factory=list, description="List of author display names")
    institutions: List[str] = Field(default_factory=list, description="Unique institutions linked to the paper")
    year: Optional[int] = Field(None, description="Publication year")
    venue: Optional[str] = Field(None, description="Publication venue/source")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    url: Optional[str] = Field(None, description="Landing page or OpenAlex URL")
    cited_by_count: Optional[int] = Field(None, description="Number of citations recorded by the provider")
    references_count: Optional[int] = Field(None, description="Number of references recorded by the provider")

    class Config:
        json_schema_extra = {
            "example": {
                "paper_id": "W4396767633",
                "title": "Unveiling the molecular mechanisms: dietary phytosterols as guardians against cardiovascular diseases",
                "abstract": "Phytosterols lower LDL cholesterol through ...",
                "authors": ["Alice Smith", "Bob Jones"],
                "institutions": ["University of Example"],
                "year": 2024,
                "venue": "Natural Products and Bioprospecting",
                "doi": "10.1007/s13659-024-00451-1",
                "url": "https://openalex.org/W4396767633",
                "cited_by_count": 12,
                "references_count": 48,
        }
    }


class PaperSummary(BaseModel):
    """Subset of catalog fields used for the All Papers view."""

    paper_id: str = Field(..., description="Canonical paper identifier")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(default_factory=list, description="Author display names")
    venue: Optional[str] = Field(None, description="Publication venue")
    year: Optional[int] = Field(None, description="Publication year")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    url: Optional[str] = Field(None, description="Landing page or OpenAlex URL")
    citation_count: Optional[int] = Field(None, description="Number of citations")
    centrality_in: Optional[float] = Field(None, description="In-degree centrality score")
    centrality_out: Optional[float] = Field(None, description="Out-degree centrality score")
    is_seed: bool = Field(False, description="True if the paper was part of the initial seed set")
    is_retracted: bool = Field(False, description="True if the paper appears on Retraction Watch")
    selected: bool = Field(False, description="True if the paper has been selected/accepted")
    mark: Literal["standard", "good", "neutral", "bad"] = Field(
        "standard", description="User annotation/mark for the paper"
    )
    nmf_topic: Optional[int] = Field(
        None, description="Assigned topic from the NMF model, if available"
    )
    lda_topic: Optional[int] = Field(
        None, description="Assigned topic from the LDA model, if available"
    )
    topics: List[str] = Field(
        default_factory=list,
        description="Topic assignments (e.g., nmf_topic:3)",
    )


class PaginatedPaperSummaries(BaseModel):
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=200)
    total: int = Field(..., ge=0)
    papers: List[PaperSummary]
    column_options: Dict[str, List[ColumnFilterOption]] = Field(
        default_factory=dict,
        description="Available column filter options keyed by column name",
    )


class ColumnOptionsPage(BaseModel):
    column: Literal["title", "authors", "venue", "year", "identifier"]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=500)
    total: int = Field(..., ge=0)
    options: List[ColumnFilterOption] = Field(default_factory=list)


class PaperMarkRequest(BaseModel):
    mark: Literal["standard", "good", "neutral", "bad"] = Field(
        ..., description="New mark for the paper"
    )


class PaperMarkResponse(BaseModel):
    paper_id: str
    mark: Literal["standard", "good", "neutral", "bad"]
