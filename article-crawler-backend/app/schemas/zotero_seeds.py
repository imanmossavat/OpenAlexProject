"""
Pydantic schemas for Zotero seed selection workflow.
Defines API contracts for Zotero integration endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ZoteroCollection(BaseModel):
    """Zotero collection metadata."""
    key: str = Field(..., description="Zotero collection key")
    name: str = Field(..., description="Collection name")
    parent_collection: Optional[str] = Field(None, description="Parent collection key if nested")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "ABC123XYZ",
                "name": "Healthcare Research",
                "parent_collection": None
            }
        }


class ZoteroCollectionsResponse(BaseModel):
    """Response containing all user's Zotero collections."""
    collections: List[ZoteroCollection] = Field(..., description="List of collections")
    total_count: int = Field(..., description="Total number of collections")
    
    class Config:
        json_schema_extra = {
            "example": {
                "collections": [
                    {"key": "ABC123", "name": "Healthcare", "parent_collection": None},
                    {"key": "DEF456", "name": "AI Research", "parent_collection": None}
                ],
                "total_count": 2
            }
        }



class ZoteroItemMetadata(BaseModel):
    """Extracted metadata from a Zotero item."""
    zotero_key: str = Field(..., description="Zotero item key")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    year: Optional[int] = Field(None, description="Publication year")
    publication: Optional[str] = Field(None, description="Publication venue")
    doi: Optional[str] = Field(None, description="DOI if available")
    url: Optional[str] = Field(None, description="URL if available")
    abstract: Optional[str] = Field(None, description="Abstract")
    item_type: str = Field(..., description="Zotero item type")
    collection_key: str = Field(..., description="Source collection key")
    
    class Config:
        json_schema_extra = {
            "example": {
                "zotero_key": "ITEM123",
                "title": "Deep Learning in Healthcare",
                "authors": ["John Doe", "Jane Smith"],
                "year": 2023,
                "publication": "Nature Medicine",
                "doi": "10.1038/s41591-023-00001-1",
                "url": "https://example.com",
                "abstract": "This paper explores...",
                "item_type": "journalArticle",
                "collection_key": "ABC123"
            }
        }


class ZoteroCollectionItemsResponse(BaseModel):
    """Response containing items from a specific collection."""
    collection_key: str = Field(..., description="Collection key")
    collection_name: str = Field(..., description="Collection name")
    items: List[ZoteroItemMetadata] = Field(..., description="List of items")
    total_count: int = Field(..., description="Total number of items")
    
    class Config:
        json_schema_extra = {
            "example": {
                "collection_key": "ABC123",
                "collection_name": "Healthcare",
                "items": [
                    {
                        "zotero_key": "ITEM123",
                        "title": "Deep Learning in Healthcare",
                        "authors": ["John Doe"],
                        "year": 2023,
                        "publication": "Nature",
                        "doi": "10.1038/example",
                        "url": "https://example.com",
                        "abstract": "Abstract...",
                        "item_type": "journalArticle",
                        "collection_key": "ABC123"
                    }
                ],
                "total_count": 1
            }
        }



class StageItemsRequest(BaseModel):
    """Request to stage items from a collection."""
    action: Literal["stage_all", "stage_selected"] = Field(
        ..., 
        description="Whether to stage all items or only selected ones"
    )
    selected_items: Optional[List[str]] = Field(
        None,
        description="List of zotero_keys to stage (required if action is 'stage_selected')"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "stage_selected",
                "selected_items": ["ITEM123", "ITEM456"]
            }
        }


class StageItemsResponse(BaseModel):
    """Response after staging items."""
    staged_count: int = Field(..., description="Number of items staged in this request")
    total_staged: int = Field(..., description="Total items in staging area")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "staged_count": 2,
                "total_staged": 5,
                "message": "Successfully staged 2 items from collection 'Healthcare'"
            }
        }


class StagedItemsResponse(BaseModel):
    """Response containing all staged items."""
    staged_items: List[ZoteroItemMetadata] = Field(..., description="All items in staging area")
    total_count: int = Field(..., description="Total staged items")
    collections: List[str] = Field(..., description="Unique collection names items are from")
    
    class Config:
        json_schema_extra = {
            "example": {
                "staged_items": [
                    {
                        "zotero_key": "ITEM123",
                        "title": "Paper 1",
                        "authors": ["Author 1"],
                        "year": 2023,
                        "publication": "Journal",
                        "doi": "10.1234/example",
                        "url": "https://example.com",
                        "abstract": "Abstract...",
                        "item_type": "journalArticle",
                        "collection_key": "ABC123"
                    }
                ],
                "total_count": 1,
                "collections": ["Healthcare", "AI Research"]
            }
        }



class ZoteroMatchCandidate(BaseModel):
    """A candidate match for manual review."""
    paper_id: str = Field(..., description="API paper ID")
    title: str = Field(..., description="Paper title from API")
    similarity: float = Field(..., description="Title similarity score (0-1)")
    year: Optional[int] = Field(None, description="Publication year")
    venue: Optional[str] = Field(None, description="Publication venue")
    doi: Optional[str] = Field(None, description="DOI")


class ZoteroMatchResult(BaseModel):
    """Result of matching a Zotero item to an API paper."""
    zotero_key: str = Field(..., description="Zotero item key")
    title: str = Field(..., description="Original Zotero title")
    matched: bool = Field(..., description="Whether a match was found")
    paper_id: Optional[str] = Field(None, description="Matched paper ID")
    confidence: float = Field(0.0, description="Match confidence (0-1)")
    match_method: Optional[str] = Field(None, description="Method used: 'doi' or 'title_search'")
    error: Optional[str] = Field(None, description="Error message if match failed")
    candidates: List[ZoteroMatchCandidate] = Field(
        default_factory=list,
        description="Alternative candidates if no auto-match"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "zotero_key": "ITEM123",
                "title": "Deep Learning in Healthcare",
                "matched": True,
                "paper_id": "W2741809807",
                "confidence": 0.95,
                "match_method": "doi",
                "error": None,
                "candidates": []
            }
        }


class ZoteroMatchRequest(BaseModel):
    """Request to match staged items against API."""
    api_provider: Literal["openalex", "semantic_scholar"] = Field(
        "openalex",
        description="API provider to use for matching"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "api_provider": "openalex"
            }
        }


class ZoteroMatchResponse(BaseModel):
    """Response containing match results for all staged items."""
    results: List[ZoteroMatchResult] = Field(..., description="Match results for each item")
    total_items: int = Field(..., description="Total items matched")
    matched_count: int = Field(..., description="Number of successful matches")
    unmatched_count: int = Field(..., description="Number of failed matches")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "zotero_key": "ITEM123",
                        "title": "Deep Learning",
                        "matched": True,
                        "paper_id": "W123",
                        "confidence": 0.95,
                        "match_method": "doi",
                        "error": None,
                        "candidates": []
                    }
                ],
                "total_items": 1,
                "matched_count": 1,
                "unmatched_count": 0
            }
        }



class ManualMatchSelection(BaseModel):
    """Manual selection for papers that need review."""
    zotero_key: str = Field(..., description="Zotero item key")
    action: Literal["select", "skip"] = Field(..., description="Select a candidate or skip")
    selected_paper_id: Optional[str] = Field(None, description="Selected paper ID (required if action is 'select')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "zotero_key": "ITEM123",
                "action": "select",
                "selected_paper_id": "W2741809807"
            }
        }


class ZoteroConfirmRequest(BaseModel):
    """Request to confirm matches and add to session."""
    action: Literal["accept_all", "skip_all"] = Field(
        ...,
        description="Accept all matched papers or skip all"
    )
    manual_selections: Optional[List[ManualMatchSelection]] = Field(
        default_factory=list,
        description="Manual selections for papers that needed review"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "accept_all",
                "manual_selections": [
                    {"zotero_key": "ITEM123", "action": "select", "selected_paper_id": "W123"},
                    {"zotero_key": "ITEM456", "action": "skip"}
                ]
            }
        }


class ZoteroConfirmResponse(BaseModel):
    """Response after confirming matches."""
    accepted_count: int = Field(..., description="Number of seeds added to session")
    skipped_count: int = Field(..., description="Number of items skipped")
    total_seeds_in_session: int = Field(..., description="Total seeds now in session")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "accepted_count": 5,
                "skipped_count": 1,
                "total_seeds_in_session": 12,
                "message": "Successfully added 5 seeds to session"
            }
        }