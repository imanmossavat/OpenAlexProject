from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from threading import RLock
from typing import Dict, Optional

from app.models.pdf_upload_session import PDFUploadSession


class PdfUploadStore(ABC):
    """Storage abstraction for PDF upload sessions."""

    @abstractmethod
    def create(self, session: PDFUploadSession) -> PDFUploadSession:
        raise NotImplementedError

    @abstractmethod
    def get(self, upload_id: str) -> Optional[PDFUploadSession]:
        raise NotImplementedError

    @abstractmethod
    def save(self, session: PDFUploadSession) -> PDFUploadSession:
        raise NotImplementedError

    @abstractmethod
    def delete(self, upload_id: str) -> Optional[PDFUploadSession]:
        raise NotImplementedError


class InMemoryPdfUploadStore(PdfUploadStore):
    """Thread-safe in-memory store for PDF upload sessions."""

    def __init__(self):
        self._sessions: Dict[str, PDFUploadSession] = {}
        self._lock = RLock()

    def create(self, session: PDFUploadSession) -> PDFUploadSession:
        with self._lock:
            self._sessions[session.upload_id] = deepcopy(session)
        return session

    def get(self, upload_id: str) -> Optional[PDFUploadSession]:
        with self._lock:
            session = self._sessions.get(upload_id)
            return deepcopy(session) if session else None

    def save(self, session: PDFUploadSession) -> PDFUploadSession:
        with self._lock:
            self._sessions[session.upload_id] = deepcopy(session)
        return session

    def delete(self, upload_id: str) -> Optional[PDFUploadSession]:
        with self._lock:
            session = self._sessions.pop(upload_id, None)
        return session

