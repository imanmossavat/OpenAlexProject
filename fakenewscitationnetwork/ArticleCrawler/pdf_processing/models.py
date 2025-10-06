
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class PDFMetadata:
    filename: str
    title: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[str] = None
    authors: Optional[str] = None
    venue: Optional[str] = None
    
    def is_valid(self) -> bool:
        return bool(self.title)
    
    def to_dict(self) -> dict:
        return {
            'filename': self.filename,
            'title': self.title,
            'doi': self.doi,
            'year': self.year,
            'authors': self.authors,
            'venue': self.venue,
        }
    
    def __str__(self) -> str:
        parts = [f"File: {self.filename}"]
        if self.title:
            parts.append(f"  Title: {self.title}")
        if self.authors:
            parts.append(f"  Authors: {self.authors}")
        if self.venue:
            parts.append(f"  Venue: {self.venue}")
        if self.year:
            parts.append(f"  Year: {self.year}")
        if self.doi:
            parts.append(f"  DOI: {self.doi}")
        return "\n".join(parts)


@dataclass
class PDFProcessingResult:
    pdf_path: Path
    metadata: Optional[PDFMetadata] = None
    success: bool = False
    error_message: Optional[str] = None
    
    def __str__(self) -> str:
        if self.success and self.metadata:
            return str(self.metadata)
        else:
            return f"File: {self.pdf_path.name}\n  Error: {self.error_message or 'Processing failed'}"


@dataclass
class APIMatchResult:
    metadata: PDFMetadata
    matched: bool = False
    paper_id: Optional[str] = None
    confidence: float = 0.0
    match_method: Optional[str] = None
    
    def __str__(self) -> str:
        status = "✓ Matched" if self.matched else "✗ Not found"
        parts = [f"{status}: {self.metadata.filename}"]
        if self.matched:
            parts.append(f"  Paper ID: {self.paper_id}")
            parts.append(f"  Confidence: {self.confidence:.2%}")
            parts.append(f"  Method: {self.match_method}")
        return "\n".join(parts)