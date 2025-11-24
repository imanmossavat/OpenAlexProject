"""Unified metadata extraction package supporting multiple file formats."""

from .models import PaperMetadata
from .dispatcher import MetadataDispatcher
from .factory import ExtractorFactory

__all__ = [
    "PaperMetadata",
    "MetadataDispatcher",
    "ExtractorFactory",
]


def extract_metadata(file_path: str) -> PaperMetadata:
    """Convenience helper for one-off metadata extraction."""
    dispatcher = MetadataDispatcher()
    return dispatcher.extract(file_path)
