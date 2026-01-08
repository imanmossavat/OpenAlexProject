from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.schemas.staging import ColumnCustomFilter


@dataclass(frozen=True)
class CatalogQuery:
    """Immutable representation of the catalog filters requested by the UI."""

    search: str = ""
    venue: Optional[str] = None
    doi: Optional[str] = None
    doi_filter: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    topic: Optional[int] = None
    topic_ids: Optional[List[int]] = None
    topic_model: Optional[str] = None
    seed_filter: Optional[str] = None
    retraction_filter: Optional[str] = None
    seed_only: bool = False
    retracted_only: bool = False
    mark_filters: Optional[List[str]] = None
    title_values: Optional[List[str]] = None
    author_values: Optional[List[str]] = None
    venue_values: Optional[List[str]] = None
    year_values: Optional[List[int]] = None
    identifier_filters: Optional[List[Dict[str, str]]] = None
    custom_filters: Optional[List[ColumnCustomFilter]] = None
    sort_by: Optional[str] = None
    descending: bool = True

    def normalized_search(self) -> str:
        return (self.search or "").strip()
