from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.seeds import MatchedSeed


SourceType = Literal["zotero", "pdf", "manual"]


class StagingPaper(BaseModel):
    """Represents a staged paper row for a session."""

    staging_id: int = Field(..., description="Unique staging row id")
    source: str = Field(..., description="Human readable source label")
    source_type: SourceType = Field(..., description="Machine friendly source type")
    title: Optional[str] = Field(None, description="Paper title")
    authors: Optional[str] = Field(None, description="Comma separated authors")
    year: Optional[int] = Field(None, description="Publication year")
    venue: Optional[str] = Field(None, description="Publication venue")
    doi: Optional[str] = Field(None, description="DOI if available")
    url: Optional[str] = Field(None, description="URL if available")
    abstract: Optional[str] = Field(None, description="Abstract text")
    source_id: Optional[str] = Field(None, description="Identifier from the source")
    is_selected: bool = Field(False, description="Whether the paper is selected for matching")


class StagingPaperCreate(BaseModel):
    """Payload for adding new staged papers."""

    source: str
    source_type: SourceType
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    source_id: Optional[str] = None
    is_selected: bool = False


class StagingPaperUpdate(BaseModel):
    """Payload for inline editing of staged papers."""

    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None


class StagingListResponse(BaseModel):
    """Paginated list response for staged papers."""

    session_id: str
    rows: List[StagingPaper]
    total_rows: int
    filtered_rows: int
    selected_count: int
    page: int
    page_size: int
    total_pages: int


class SelectionUpdateRequest(BaseModel):
    """Bulk selection toggle request."""

    staging_ids: List[int]
    is_selected: bool


class BulkRemoveRequest(BaseModel):
    """Bulk removal request by staging ids."""

    staging_ids: List[int]


class SelectionUpdateResponse(BaseModel):
    """Response payload after toggling selection."""

    updated_count: int
    selected_count: int


class BulkRemoveResponse(BaseModel):
    """Response payload after removing staged rows."""

    removed_count: int
    total_rows: int


class MatchSelectedRequest(BaseModel):
    """Request payload to match currently selected staged rows."""

    api_provider: str = Field(default="openalex", description="API provider to use for matching")


class StagingMatchRow(BaseModel):
    """Single staging row match result."""

    staging_id: int
    staging: StagingPaper
    matched: bool
    match_method: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    matched_seed: Optional[MatchedSeed] = None


class StagingMatchResponse(BaseModel):
    """Response after running matching on selected rows."""

    session_id: str
    total_selected: int
    matched_rows: List[StagingMatchRow]
    unmatched_rows: List[StagingMatchRow]


class ConfirmMatchesRequest(BaseModel):
    """Confirm which staging rows should become seeds."""

    staging_ids: Optional[List[int]] = Field(
        default=None,
        description="Optional subset of staging IDs to confirm. Defaults to all matched rows.",
    )
