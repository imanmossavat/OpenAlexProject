from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock
from typing import Dict, Optional

from app.schemas.seed_session import SeedSession


class SeedSessionStore(ABC):
    """Abstract contract for storing seed sessions."""

    @abstractmethod
    def create(self, session: SeedSession) -> SeedSession:
        raise NotImplementedError

    @abstractmethod
    def get(self, session_id: str) -> Optional[SeedSession]:
        raise NotImplementedError

    @abstractmethod
    def save(self, session: SeedSession) -> SeedSession:
        raise NotImplementedError

    @abstractmethod
    def delete(self, session_id: str) -> None:
        raise NotImplementedError


class InMemorySeedSessionStore(SeedSessionStore):
    """Thread-safe in-memory implementation of the session store."""

    def __init__(self):
        self._sessions: Dict[str, SeedSession] = {}
        self._lock = RLock()

    def create(self, session: SeedSession) -> SeedSession:
        with self._lock:
            self._sessions[session.session_id] = session.model_copy(deep=True)
        return session

    def get(self, session_id: str) -> Optional[SeedSession]:
        with self._lock:
            session = self._sessions.get(session_id)
            return session.model_copy(deep=True) if session else None

    def save(self, session: SeedSession) -> SeedSession:
        with self._lock:
            self._sessions[session.session_id] = session.model_copy(deep=True)
        return session

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

