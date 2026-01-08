import logging
from pathlib import Path
from typing import Optional

from ArticleCrawler.pdf_processing.docker_manager import DockerManager
from ArticleCrawler.pdf_processing.grobid_client import GrobidClientWrapper
from ArticleCrawler.pdf_processing.metadata_extractor import PDFMetadataExtractor

from .base import BaseExtractor
from ..models import PaperMetadata
from ..utils import parse_author_list


class PdfExtractor(BaseExtractor):
    """Extract metadata from PDFs via GROBID."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        docker_manager: Optional[DockerManager] = None,
        grobid_client: Optional[GrobidClientWrapper] = None,
        metadata_extractor: Optional[PDFMetadataExtractor] = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._docker_manager = docker_manager or DockerManager(logger=self._logger)
        self._grobid_client = grobid_client or GrobidClientWrapper(logger=self._logger)
        self._metadata_extractor = metadata_extractor or PDFMetadataExtractor(
            logger=self._logger
        )

    def extract(self, path: str) -> PaperMetadata:
        path_obj = Path(path)
        if not path_obj.exists():
            self._logger.error("PDF not found: %s", path)
            return PaperMetadata()

        if not self._docker_manager.is_grobid_running():
            self._logger.error("GROBID service is not running.")
            return PaperMetadata()

        try:
            xml_results = self._grobid_client.process_pdfs([path_obj])
        except Exception as exc:
            self._logger.error("Failed to process %s via GROBID: %s", path, exc)
            return PaperMetadata()

        if path_obj not in xml_results:
            self._logger.warning("No XML output for %s", path)
            return PaperMetadata()

        xml_content = xml_results[path_obj]
        pdf_metadata = self._metadata_extractor.extract(xml_content, path_obj.name)
        if not pdf_metadata:
            self._logger.warning("Metadata extractor returned nothing for %s", path)
            return PaperMetadata()

        authors = parse_author_list(pdf_metadata.authors or "")

        return PaperMetadata(
            title=pdf_metadata.title,
            authors=authors,
            abstract=None,  # GROBID header does not provide abstract here
            year=pdf_metadata.year,
            doi=pdf_metadata.doi,
            venue=pdf_metadata.venue,
        )
