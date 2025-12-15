from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ExperimentSummary(BaseModel):
    """Metadata describing a saved crawler experiment."""

    job_id: str
    name: str
    display_name: Optional[str] = None
    total_seeds: int
    total_keywords: int
    library_path: Optional[str] = None
    library_name: Optional[str] = None
    updated_at: datetime


class ExperimentListResponse(BaseModel):
    """Paginated response for saved experiments."""

    total: int = Field(..., description="Total experiments available")
    page: int
    page_size: int
    experiments: List[ExperimentSummary]
    root_path: Optional[str] = Field(
        default=None, description="Filesystem path scanned for experiments"
    )


class LoadExperimentRequest(BaseModel):
    """Request to hydrate a session from a saved experiment."""

    session_id: str


class LoadExperimentResponse(BaseModel):
    """Response after loading an experiment into a session."""

    session_id: str
    job_id: str
    experiment: ExperimentSummary


class LoadExperimentByPathRequest(BaseModel):
    """Request to hydrate a session from an absolute experiment path."""

    session_id: str
    experiment_path: str
