from pathlib import Path
from typing import Optional
import logging

import magic

from .factory import ExtractorFactory
from .models import PaperMetadata


class MetadataDispatcher:
    """Detects MIME type and delegates to the correct extractor."""

    def __init__(
        self,
        factory: Optional[ExtractorFactory] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._factory = factory or ExtractorFactory()
        self._logger = logger or logging.getLogger(__name__)

    def extract(self, file_path: str) -> PaperMetadata:
        """Extract metadata from the supplied file."""
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        mime_type = self._detect_mime(path_obj)
        self._logger.debug("Detected %s for %s", mime_type, file_path)

        extractor = self._factory.create(mime_type)
        self._logger.debug("Dispatching to %s", extractor.__class__.__name__)
        metadata = extractor.extract(str(path_obj))
        return metadata

    def can_extract(self, file_path: str) -> bool:
        """Return True when a file type is supported."""
        try:
            mime = self._detect_mime(Path(file_path))
            return self._factory.supports(mime)
        except Exception:
            return False

    EXTENSION_FALLBACKS = {
        ".tex": "text/x-tex",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xml": "text/xml",
    }

    def _detect_mime(self, file_path: Path) -> str:
        """Detect MIME type using python-magic with extension fallbacks."""
        mime_type = magic.from_file(str(file_path), mime=True)
        if mime_type in {"text/plain", "application/octet-stream"}:
            ext = file_path.suffix.lower()
            return self.EXTENSION_FALLBACKS.get(ext, mime_type)
        return mime_type
