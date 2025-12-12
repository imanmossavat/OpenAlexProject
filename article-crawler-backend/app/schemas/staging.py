from datetime import datetime
from typing import Dict, List, Literal, Optional, get_args

from pydantic import BaseModel, Field, validator

from ArticleCrawler.normalization import normalize_venue

from app.schemas.seeds import MatchedSeed


SourceType = Literal["zotero", "pdf", "manual"]
TextFilterOperator = Literal[
    "equals",
    "not_equals",
    "begins_with",
    "not_begins_with",
    "ends_with",
    "not_ends_with",
    "contains",
    "not_contains",
]
NumberFilterOperator = Literal[
    "equals",
    "not_equals",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "between",
    "not_between",
]
FilterOperator = Literal[
    "equals",
    "not_equals",
    "begins_with",
    "not_begins_with",
    "ends_with",
    "not_ends_with",
    "contains",
    "not_contains",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "between",
    "not_between",
]
TEXT_FILTER_COLUMNS = {"title", "authors", "venue", "identifier"}
NUMBER_FILTER_COLUMNS = {"year"}
TEXT_FILTER_OPERATOR_VALUES = set(get_args(TextFilterOperator))
NUMBER_FILTER_OPERATOR_VALUES = set(get_args(NumberFilterOperator))


class StagingPaper(BaseModel):
    """Represents a staged paper row for a session."""

    staging_id: int = Field(..., description="Unique staging row id")
    source: str = Field(..., description="Human readable source label")
    source_type: SourceType = Field(..., description="Machine friendly source type")
    is_library_seed: bool = Field(False, description="True when row originated from a loaded library")
    title: Optional[str] = Field(None, description="Paper title")
    authors: Optional[str] = Field(None, description="Comma separated authors")
    year: Optional[int] = Field(None, description="Publication year")
    venue: Optional[str] = Field(None, description="Publication venue")
    doi: Optional[str] = Field(None, description="DOI if available")
    url: Optional[str] = Field(None, description="URL if available")
    abstract: Optional[str] = Field(None, description="Abstract text")
    is_retracted: bool = Field(False, description="Flag when the paper matches Retraction Watch")
    retraction_reason: Optional[str] = Field(
        default=None,
        description="Optional text explaining why the paper is marked retracted",
    )
    retraction_date: Optional[str] = Field(
        default=None,
        description="Date provided by Retraction Watch for this entry",
    )
    retraction_checked_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the row was last checked for retractions",
    )
    source_id: Optional[str] = Field(None, description="Identifier from the source")
    is_selected: bool = Field(False, description="Whether the paper is selected for matching")
    source_file_id: Optional[str] = Field(
        default=None,
        description="Internal identifier for the uploaded source file",
        exclude=True,
    )
    source_file_name: Optional[str] = Field(
        default=None,
        description="Original filename of the uploaded source file",
    )

    @validator("venue", pre=True, always=True)
    def _normalize_venue_field(cls, value):
        return _normalize_venue_value(value)


class StagingPaperCreate(BaseModel):
    """Payload for adding new staged papers."""

    source: str
    source_type: SourceType
    is_library_seed: bool = Field(False, description="True when row originated from a loaded library")
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    is_retracted: bool = False
    retraction_reason: Optional[str] = None
    retraction_date: Optional[str] = None
    retraction_checked_at: Optional[datetime] = None
    source_id: Optional[str] = None
    is_selected: bool = False
    source_file_id: Optional[str] = None
    source_file_name: Optional[str] = None

    @validator("venue", pre=True, always=True)
    def _normalize_venue_field(cls, value):
        return _normalize_venue_value(value)


class StagingPaperUpdate(BaseModel):
    """Payload for inline editing of staged papers."""

    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None

    @validator("venue", pre=True, always=True)
    def _normalize_venue_field(cls, value):
        return _normalize_venue_value(value)


class ColumnFilterOption(BaseModel):
    """Aggregated option for column-level filtering."""

    value: str
    label: str
    count: int
    meta: Optional[Dict[str, str]] = None


class ColumnCustomFilter(BaseModel):
    """Advanced text/number filter applied to a specific column."""

    column: Literal["title", "authors", "venue", "identifier", "year"]
    operator: FilterOperator
    value: str
    value_to: Optional[str] = None


class StagingListResponse(BaseModel):
    """Paginated list response for staged papers."""

    session_id: str
    rows: List[StagingPaper]
    total_rows: int
    filtered_rows: int
    selected_count: int
    retracted_count: int = Field(0, description="How many staged rows are currently marked retracted")
    page: int
    page_size: int
    total_pages: int
    column_options: Dict[str, List[ColumnFilterOption]] = Field(default_factory=dict)


class RetractionCheckResponse(BaseModel):
    """Result summary after running a retraction check."""

    session_id: str
    total_rows: int
    checked_rows: int
    retracted_count: int
    skipped_without_doi: int
    checked_at: datetime


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


def _normalize_venue_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = normalize_venue(value)
    if normalized:
        return normalized
    stripped = value.strip()
    return stripped or None


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
