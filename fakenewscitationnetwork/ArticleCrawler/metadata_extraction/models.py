from dataclasses import dataclass, field
from typing import List, Optional

from ..normalization import normalize_venue


@dataclass
class PaperMetadata:
    """Unified metadata structure produced by all extractors."""

    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    abstract: Optional[str] = None
    year: Optional[str] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    venue_raw: Optional[str] = None

    def __post_init__(self) -> None:
        if self.authors is None:
            self.authors = []
        if self.venue_raw is None:
            self.venue_raw = self.venue
        normalized = normalize_venue(self.venue_raw)
        if normalized:
            self.venue = normalized
        elif self.venue_raw:
            self.venue = self.venue_raw.strip()

    def is_complete(self) -> bool:
        """Return True when core fields are populated."""
        return bool(self.title and self.authors and self.abstract)

    def completeness_score(self) -> float:
        """Return ratio of populated fields to available fields."""
        fields = [
            self.title,
            self.authors,
            self.abstract,
            self.year,
            self.doi,
            self.venue,
        ]
        populated = sum(1 for value in fields if value)
        return populated / len(fields)
