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
from app.services.seeds.helpers import SeedSessionManager


class SeedSessionService:
    def __init__(
        self,
        logger: logging.Logger,
        store: Optional[SeedSessionStore] = None,
        session_manager: Optional[SeedSessionManager] = None,
    ):
        self.logger = logger
        self._store = store or InMemorySeedSessionStore()
        self._session_manager = session_manager or SeedSessionManager()
    
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
        
        result = self._session_manager.add_seeds(session, new_seeds)
        self._store.save(session)
        
        self.logger.info(
            "Added %s seeds to session %s (%s duplicates skipped)",
            result.added_count,
            session_id,
            result.duplicate_count,
        )
        
        return AddSeedsToSessionResponse(
            session_id=session_id,
            added_count=result.added_count,
            duplicate_count=result.duplicate_count,
            total_seeds=result.total_seeds,
        )
    
    def remove_seed_from_session(
        self, 
        session_id: str, 
        paper_id: str
    ) -> SessionSeedsResponse:
        session = self._get_session_or_raise(session_id)
        
        removed = self._session_manager.remove_seed(session, paper_id)
        if removed:
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
        result = self._session_manager.replace_seeds(session, new_seeds)
        self._store.save(session)
        self.logger.info("Replaced seeds for session %s with %s items", session_id, len(new_seeds))
        return AddSeedsToSessionResponse(
            session_id=session_id,
            added_count=result.added_count,
            duplicate_count=0,
            total_seeds=result.total_seeds,
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
