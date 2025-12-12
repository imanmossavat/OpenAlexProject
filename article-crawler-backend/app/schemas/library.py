from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from app.schemas.seeds import MatchedSeed


class LibraryDetailsRequest(BaseModel):
    name: str = Field(..., description="Library name")
    path: Optional[str] = Field(None, description="Absolute path to create the library (optional: defaults to .libraries)")
    description: Optional[str] = Field(None, description="Optional description")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError("Library name cannot be empty")
        return v


class LibraryDetailsResponse(BaseModel):
    session_id: str
    name: str
    path: str
    description: Optional[str] = None


class LibraryPreviewResponse(BaseModel):
    session_id: str
    name: str
    path: str
    description: Optional[str] = None
    total_papers: int = Field(..., description="Total seed papers selected")


class CreateLibraryResponse(BaseModel):
    session_id: str
    name: str
    base_path: str
    total_requested: int
    saved_count: int
    message: str
    papers: List["LibraryPaper"] = Field(default_factory=list, description="Papers saved in the library")


class LibraryPaper(BaseModel):
    paper_id: str
    title: str = ""
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None


CreateLibraryResponse.model_rebuild()


class LibraryInfo(BaseModel):
    name: str
    path: str
    description: Optional[str] = None
    paper_count: int = 0
    api_provider: Optional[str] = None
    created_at: Optional[str] = None


class LibraryListResponse(BaseModel):
    libraries: List[LibraryInfo] = Field(default_factory=list)
    total: int = Field(..., description="Total libraries that match the current query")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")


class LibrarySelectRequest(BaseModel):
    path: str = Field(..., description="Absolute path to an existing library")
    name: Optional[str] = Field(None, description="Optional library name")


class LibrarySelectionResponse(BaseModel):
    session_id: str
    name: str
    path: str
    description: Optional[str] = None
    paper_count: int


class AddLibrarySeedsRequest(BaseModel):
    paper_ids: Optional[List[str]] = Field(None, description="Paper IDs to add to the library")
    api_provider: Optional[str] = Field(None, description="Override API provider (default: from library config)")
    seeds: Optional[List[MatchedSeed]] = Field(None, description="Matched seeds to add to the library")


class AddLibrarySeedsResponse(BaseModel):
    session_id: str
    api_provider: str
    requested: int
    added_count: int
    skipped_existing: List[str] = Field(default_factory=list)
    failed: List[str] = Field(default_factory=list)
    added_ids: List[str] = Field(default_factory=list)


class RemoveLibrarySeedsRequest(BaseModel):
    paper_ids: List[str] = Field(..., description="Paper IDs to remove from the library")


class RemoveLibrarySeedsResponse(BaseModel):
    session_id: str
    requested: int
    removed_count: int
    not_found: List[str] = Field(default_factory=list)
    removed_ids: List[str] = Field(default_factory=list)


class LibraryContentsResponse(BaseModel):
    session_id: str
    name: str
    path: str
    papers: List[LibraryPaper] = Field(default_factory=list)
    total_papers: int


class ApplySessionSeedsRequest(BaseModel):
    api_provider: Optional[str] = Field(
        default=None,
        description="Override API provider when adding session seeds (default: library config)"
    )


class ApplySessionSeedsResponse(BaseModel):
    session_id: str
    api_provider: str
    requested: int
    added_count: int
    skipped_existing: List[str] = Field(default_factory=list)
    failed: List[str] = Field(default_factory=list)
    added_ids: List[str] = Field(default_factory=list)
