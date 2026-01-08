from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from app.schemas.pdf_seeds import (
    PDFExtractionResult,
    PDFMatchResult,
    PDFMetadata,
)


@dataclass
class PDFUploadSession:
    """Represents a PDF upload session stored between API calls."""

    upload_id: str
    temp_dir: Path
    pdf_paths: List[Path] = field(default_factory=list)
    file_lookup: Dict[str, Path] = field(default_factory=dict)
    extraction_results: List[PDFExtractionResult] = field(default_factory=list)
    reviewed_metadata: List[PDFMetadata] = field(default_factory=list)
    match_results: List[PDFMatchResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

