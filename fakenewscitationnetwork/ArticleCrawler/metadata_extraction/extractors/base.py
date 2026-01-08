from abc import ABC, abstractmethod

from ..models import PaperMetadata


class BaseExtractor(ABC):
    """Abstract base class for metadata extractors."""

    @abstractmethod
    def extract(self, path: str) -> PaperMetadata:
        """Return metadata for the supplied file."""
        raise NotImplementedError
