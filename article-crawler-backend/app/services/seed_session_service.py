import logging
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.schemas.seed_session import (
    SeedSession,
    StartSessionRequest,
    StartSessionResponse,
    SessionSeedsResponse,
    AddSeedsToSessionResponse
)
from app.schemas.seeds import MatchedSeed
from app.core.exceptions import LibraryNotFoundException
from app.core.stores.seed_session_store import (
    InMemorySeedSessionStore,
    SeedSessionStore,
)


class SeedSessionService:

    
    def __init__(self, logger: logging.Logger, store: Optional[SeedSessionStore] = None):
        self.logger = logger
        self._store = store or InMemorySeedSessionStore()
    
    def start_session(self, request: StartSessionRequest) -> StartSessionResponse:

        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        session = SeedSession(
            session_id=session_id,
            use_case=request.use_case,
            seeds=[],
            created_at=now,
            updated_at=now
        )
        
        self._store.create(session)
        self.logger.info(f"Started seed session {session_id} for use case: {request.use_case}")
        
        return StartSessionResponse(
            session_id=session_id,
            use_case=request.use_case,
            created_at=now
        )
    
    def get_session(self, session_id: str) -> SessionSeedsResponse:

        session = self._get_session_or_raise(session_id)

        return SessionSeedsResponse(
            session_id=session.session_id,
            use_case=session.use_case,
            seeds=session.seeds,
            total_seeds=len(session.seeds),
            created_at=session.created_at,
            updated_at=session.updated_at
        )
    
    def add_seeds_to_session(
        self, 
        session_id: str, 
        new_seeds: List[MatchedSeed]
    ) -> AddSeedsToSessionResponse:

        session = self._get_session_or_raise(session_id)
        
        existing_ids = {seed.paper_id for seed in session.seeds}
        
        added_count = 0
        duplicate_count = 0
        
        for seed in new_seeds:
            if seed.paper_id not in existing_ids:
                session.seeds.append(seed)
                existing_ids.add(seed.paper_id)
                added_count += 1
            else:
                duplicate_count += 1
        
        session.updated_at = datetime.now(timezone.utc)
        self._store.save(session)
        
        self.logger.info(
            f"Added {added_count} seeds to session {session_id} "
            f"({duplicate_count} duplicates skipped)"
        )
        
        return AddSeedsToSessionResponse(
            session_id=session_id,
            added_count=added_count,
            duplicate_count=duplicate_count,
            total_seeds=len(session.seeds)
        )
    
    def remove_seed_from_session(
        self, 
        session_id: str, 
        paper_id: str
    ) -> SessionSeedsResponse:
        session = self._get_session_or_raise(session_id)
        
        initial_count = len(session.seeds)
        session.seeds = [s for s in session.seeds if s.paper_id != paper_id]
        removed_count = initial_count - len(session.seeds)
        
        if removed_count > 0:
            session.updated_at = datetime.now(timezone.utc)
            self._store.save(session)
            self.logger.info(f"Removed seed {paper_id} from session {session_id}")
        else:
            self.logger.warning(f"Seed {paper_id} not found in session {session_id}")
        
        return self.get_session(session_id)

    def set_seeds_for_session(
        self,
        session_id: str,
        new_seeds: List[MatchedSeed]
    ) -> AddSeedsToSessionResponse:
        session = self._get_session_or_raise(session_id)
        session.seeds = list(new_seeds)
        session.updated_at = datetime.now(timezone.utc)
        self._store.save(session)
        self.logger.info(
            f"Replaced seeds for session {session_id} with {len(new_seeds)} items"
        )
        return AddSeedsToSessionResponse(
            session_id=session_id,
            added_count=len(new_seeds),
            duplicate_count=0,
            total_seeds=len(new_seeds)
        )
    
    def finalize_session(self, session_id: str) -> List[MatchedSeed]:

        session = self._get_session_or_raise(session_id)
        
        self.logger.info(
            f"Finalized session {session_id} with {len(session.seeds)} seeds"
        )
        
        return session.seeds
    
    def delete_session(self, session_id: str) -> None:

        session = self._store.get(session_id)
        if not session:
            raise LibraryNotFoundException(f"Session {session_id} not found")
        self._store.delete(session_id)
        self.logger.info(f"Deleted session {session_id}")
    
    def _get_session_or_raise(self, session_id: str) -> SeedSession:
        """Get session or raise exception if not found."""
        session = self._store.get(session_id)
        if not session:
            raise LibraryNotFoundException(f"Session {session_id} not found")
        return session
