from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PDFMetadata(BaseModel):
    """Extracted metadata from a PDF."""
    filename: str
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None


class PDFExtractionResult(BaseModel):
    """Result of extracting metadata from a single PDF."""
    filename: str
    success: bool
    metadata: Optional[PDFMetadata] = None
    error: Optional[str] = None


class PDFMatchResult(BaseModel):
    """Result of matching PDF metadata against API."""
    filename: str
    metadata: PDFMetadata
    matched: bool
    paper_id: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    confidence: float = 0.0
    match_method: Optional[str] = None


class PDFUploadResponse(BaseModel):
    """Response after uploading PDFs."""
    upload_id: str
    filenames: List[str]
    total_files: int
    created_at: datetime


class PDFExtractionResponse(BaseModel):
    """Response after extracting metadata from PDFs."""
    upload_id: str
    results: List[PDFExtractionResult]
    successful_count: int
    failed_count: int


class PDFMetadataReview(BaseModel):
    """User's review of extracted metadata."""
    filename: str
    action: str = Field(..., description="accept, edit, or skip")
    edited_metadata: Optional[PDFMetadata] = None


class PDFReviewRequest(BaseModel):
    """Request to submit reviewed PDF metadata."""
    reviews: List[PDFMetadataReview]


class PDFMatchResponse(BaseModel):
    """Response after matching PDFs against API."""
    upload_id: str
    results: List[PDFMatchResult]
    matched_count: int
    unmatched_count: int


class PDFConfirmRequest(BaseModel):
    """Request to confirm which PDFs to add as seeds."""
    action: str = Field(..., description="use_all or skip_all")


class PDFConfirmResponse(BaseModel):
    """Response after confirming PDF seeds."""
    upload_id: str
    added_count: int
    total_seeds_in_session: int


class PDFStageResponse(BaseModel):
    """Response after staging reviewed PDFs."""
    upload_id: str
    staged_count: int
    total_staged: int
