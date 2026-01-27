from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class ZoteroExportRequest(BaseModel):
    """Payload describing which papers to export and where to send them."""

    paper_ids: List[str] = Field(..., min_length=1, description="List of paper IDs from the job catalog.")
    collection_key: Optional[str] = Field(
        default=None,
        description="Existing Zotero collection key that should receive the export.",
    )
    collection_name: Optional[str] = Field(
        default=None,
        description="Friendly name of the destination collection. Required if collection_key is omitted.",
    )
    create_collection: bool = Field(
        default=False,
        description="Create the collection if collection_name is provided and does not exist.",
    )
    dedupe: bool = Field(
        default=True,
        description="Skip exporting papers that already exist in the destination collection (by DOI or URL).",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Additional Zotero tags applied to every exported paper.",
    )

    @model_validator(mode="after")
    def validate_collection_target(cls, values: "ZoteroExportRequest"):
        if not values.collection_key and not values.collection_name:
            raise ValueError("collection_key or collection_name must be provided.")
        return values


class ZoteroExportResponse(BaseModel):
    """Summary of an export run."""

    created: int = Field(..., description="Number of Zotero items created successfully.")
    skipped: int = Field(..., description="Number of papers skipped due to deduplication rules.")
    failed: int = Field(..., description="Number of papers that failed to export.")
    created_paper_ids: List[str] = Field(default_factory=list, description="IDs of the papers created in Zotero.")
    skipped_papers: Dict[str, str] = Field(
        default_factory=dict, description="Map of paper IDs to skip reasons."
    )
    failed_papers: Dict[str, str] = Field(
        default_factory=dict, description="Map of paper IDs to failure messages."
    )
