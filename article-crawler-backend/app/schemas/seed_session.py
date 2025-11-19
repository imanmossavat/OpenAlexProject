from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.seeds import MatchedSeed


class SeedSession(BaseModel):
    """A seed selection session."""
    session_id: str
    use_case: str = Field(description="Use case: crawler_wizard or library_creation")
    seeds: List[MatchedSeed] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class StartSessionRequest(BaseModel):
    """Request to start a new seed session."""
    use_case: str = Field(
        default="crawler_wizard",
        description="Use case for this session: crawler_wizard or library_creation"
    )


class StartSessionResponse(BaseModel):
    """Response after starting a session."""
    session_id: str
    use_case: str
    created_at: datetime


class SessionSeedsResponse(BaseModel):
    """Response showing all seeds in a session."""
    session_id: str
    use_case: str
    seeds: List[MatchedSeed]
    total_seeds: int
    created_at: datetime
    updated_at: datetime


class AddSeedsToSessionRequest(BaseModel):
    """Request to add seeds to a session."""
    seeds: List[MatchedSeed]


class AddSeedsToSessionResponse(BaseModel):
    """Response after adding seeds to session."""
    session_id: str
    added_count: int
    duplicate_count: int
    total_seeds: int


class FinalizeSessionResponse(BaseModel):
    """Response after finalizing a session."""
    session_id: str
    total_seeds: int
    seeds: List[MatchedSeed]