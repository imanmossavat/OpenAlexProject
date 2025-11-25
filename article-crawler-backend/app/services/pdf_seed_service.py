import logging
import uuid
from typing import List, Dict, Optional
from pathlib import Path

from fastapi import UploadFile

from ArticleCrawler.pdf_processing.docker_manager import DockerManager
from ArticleCrawler.pdf_processing.api_matcher import APIMetadataMatcher
from ArticleCrawler.metadata_extraction import MetadataDispatcher, PaperMetadata as ExtractedMetadata
from ArticleCrawler.api.api_factory import create_api_provider

from app.schemas.pdf_seeds import (
    PDFMetadata,
    PDFExtractionResult,
    PDFMatchResult,
    PDFUploadResponse,
    PDFExtractionResponse,
    PDFMatchResponse,
    PDFMetadataReview
)
from app.core.exceptions import InvalidInputException, CrawlerException
from app.core.stores.pdf_upload_store import (
    InMemoryPdfUploadStore,
    PdfUploadStore,
)
from app.core.storage.file_storage import (
    FileStorageAdapter,
    LocalTempFileStorage,
)
from app.models.pdf_upload_session import PDFUploadSession
from app.services.source_file_service import SourceFileService


class PDFSeedService:

    
    MAX_FILE_SIZE_MB = 30
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".html", ".htm", ".xml", ".tex"}
    
    def __init__(
        self,
        logger: logging.Logger,
        upload_store: Optional[PdfUploadStore] = None,
        file_storage: Optional[FileStorageAdapter] = None,
        source_file_service: Optional[SourceFileService] = None,
    ):
        self.logger = logger
        self._store = upload_store or InMemoryPdfUploadStore()
        self._storage = file_storage or LocalTempFileStorage()
        self._source_file_service = source_file_service
        
        self.docker_manager = DockerManager(logger=logger)
        self.metadata_dispatcher = MetadataDispatcher(logger=logger)
    
    def check_grobid_availability(self) -> tuple[bool, Optional[str]]:

        if self.docker_manager.is_grobid_running():
            return True, None
        
        error_msg = (
            "GROBID service is not running. "
            "Please start it with: docker run -d -p 8070:8070 lfoppiano/grobid:0.8.2"
        )
        return False, error_msg
    
    def upload_pdfs(self, files: List[UploadFile]) -> PDFUploadResponse:

        if self._requires_grobid(files):
            is_available, error_msg = self.check_grobid_availability()
            if not is_available:
                raise CrawlerException(error_msg)
        
        upload_id = str(uuid.uuid4())
        temp_dir = self._storage.create_temp_dir(prefix=f"pdf_upload_{upload_id}_")
        
        session = PDFUploadSession(upload_id, temp_dir)
        
        filenames = []
        for file in files:
            file.file.seek(0, 2)
            file_size_mb = file.file.tell() / (1024 * 1024)
            file.file.seek(0)
            
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                self.logger.warning(f"File {file.filename} exceeds size limit ({file_size_mb:.1f}MB)")
                continue

            if not self._is_supported_file(file.filename):
                self.logger.warning(f"Unsupported file type for {file.filename}; skipping.")
                continue
            
            safe_name = self._sanitize_filename(file.filename, temp_dir)
            pdf_path = self._storage.save_upload(temp_dir, safe_name, file)
            
            session.pdf_paths.append(pdf_path)
            session.file_lookup[safe_name] = pdf_path
            filenames.append(safe_name)
        
        self._store.create(session)
        
        self.logger.info(f"Saved {len(filenames)} PDFs for upload {upload_id}")
        
        return PDFUploadResponse(
            upload_id=upload_id,
            filenames=filenames,
            total_files=len(filenames),
            created_at=session.created_at
        )
    
    def extract_metadata(self, upload_id: str) -> PDFExtractionResponse:
        session = self._get_session(upload_id)
        
        self.logger.info(f"Extracting metadata from {len(session.pdf_paths)} PDFs")
        
        extraction_results = []
        successful_count = 0
        
        for file_path in session.pdf_paths:
            result = self._extract_file_metadata(file_path)
            extraction_results.append(result)
            if result.success:
                successful_count += 1
        
        session.extraction_results = extraction_results
        self._store.save(session)
        
        self.logger.info(f"Extraction complete: {successful_count}/{len(extraction_results)} successful")
        
        return PDFExtractionResponse(
            upload_id=upload_id,
            results=extraction_results,
            successful_count=successful_count,
            failed_count=len(extraction_results) - successful_count
        )
    
    def _extract_file_metadata(self, file_path: Path) -> PDFExtractionResult:
        filename = file_path.name
        
        if self._is_pdf(filename):
            is_available, error_msg = self.check_grobid_availability()
            if not is_available:
                return PDFExtractionResult(
                    filename=filename,
                    success=False,
                    error=error_msg
                )
        
        try:
            metadata = self.metadata_dispatcher.extract(str(file_path))
        except Exception as exc:
            self.logger.error(f"Failed to extract metadata from {filename}: {exc}")
            return PDFExtractionResult(
                filename=filename,
                success=False,
                error=str(exc)
            )
        
        pdf_metadata = self._to_schema_metadata(filename, metadata)
        if not self._has_metadata(pdf_metadata):
            return PDFExtractionResult(
                filename=filename,
                success=False,
                error="No metadata extracted"
            )
        
        return PDFExtractionResult(
            filename=filename,
            success=True,
            metadata=pdf_metadata
        )
    
    def review_metadata(
        self,
        upload_id: str,
        reviews: List[PDFMetadataReview]
    ) -> Dict[str, any]:

        session = self._get_session(upload_id)
        
        reviewed_metadata = []
        
        for review in reviews:
            if review.action == "skip":
                continue
            
            elif review.action == "accept":
                for result in session.extraction_results:
                    if result.filename == review.filename and result.metadata:
                        reviewed_metadata.append(result.metadata)
                        break
            
            elif review.action == "edit":
                if review.edited_metadata:
                    reviewed_metadata.append(review.edited_metadata)
            
            else:
                raise InvalidInputException(f"Invalid action: {review.action}")
        
        session.reviewed_metadata = reviewed_metadata
        self._store.save(session)
        
        return {
            "upload_id": upload_id,
            "reviewed_count": len(reviewed_metadata),
            "message": "Metadata reviews processed"
        }
    
    def match_against_api(
        self,
        upload_id: str,
        api_provider: str = "openalex"
    ) -> PDFMatchResponse:

        session = self._get_session(upload_id)
        
        if not session.reviewed_metadata:
            raise InvalidInputException("No reviewed metadata to match. Please review metadata first.")
        
        self.logger.info(f"Matching {len(session.reviewed_metadata)} PDFs against {api_provider}")
        
        api = create_api_provider(api_provider)
        
        matcher = APIMetadataMatcher(api, logger=self.logger)
        
        class MetadataWrapper:
            def __init__(self, m):
                self.filename = m.filename
                self.title = m.title
                self.authors = m.authors
                self.year = m.year
                self.doi = m.doi
                self.venue = m.venue
        
        metadata_list = [MetadataWrapper(m) for m in session.reviewed_metadata]
        
        try:
            api_match_results = matcher.match_metadata(metadata_list)
        except Exception as e:
            self.logger.warning(f"Bulk match failed, falling back to per-item matching: {e}")
            api_match_results = []
            class _FallbackMatchResult:
                def __init__(self, md, matched=False, paper_id=None, confidence=0.0, match_method=None):
                    self.metadata = md
                    self.matched = matched
                    self.paper_id = paper_id
                    self.confidence = confidence
                    self.match_method = match_method
            for md in metadata_list:
                try:
                    res = matcher._match_single(md)
                    api_match_results.append(res)
                except Exception as ie:
                    self.logger.warning(f"Match failed for {getattr(md, 'filename', 'unknown')}: {ie}")
                    api_match_results.append(_FallbackMatchResult(md, matched=False))
        
        match_results = []
        matched_count = 0

        def _get(obj, name):
            if obj is None:
                return None
            if isinstance(obj, dict):
                return obj.get(name)
            return getattr(obj, name, None)

        for result in api_match_results:
            meta = getattr(result, 'metadata', None)
            filename = _get(meta, 'filename') or "unknown"
            title_orig = _get(meta, 'title')
            authors_orig = _get(meta, 'authors')
            year_orig = _get(meta, 'year')
            doi_orig = _get(meta, 'doi')
            venue_orig = _get(meta, 'venue')

            if result.matched:
                paper = None
                try:
                    if hasattr(api, 'get_paper_metadata_only'):
                        paper = api.get_paper_metadata_only(result.paper_id)
                    else:
                        paper = api.get_paper(result.paper_id)
                except Exception as e:
                    self.logger.warning(f"Failed to fetch paper {result.paper_id}: {e}")
                    paper = None

                if paper is None:
                    self.logger.warning(f"Paper {result.paper_id} could not be fetched, treating as unmatched")
                    match_results.append(PDFMatchResult(
                        filename=filename,
                        metadata=PDFMetadata(
                            filename=filename,
                            title=title_orig,
                            authors=authors_orig,
                            year=year_orig,
                            doi=doi_orig,
                            venue=venue_orig
                        ),
                        matched=False
                    ))
                    continue

                try:
                    if isinstance(paper, dict):
                        title = paper.get('title')
                        authors_list = paper.get('authorships', [])
                        year = paper.get('publication_year')
                        primary_location = paper.get('primary_location', {})
                        venue = None
                        if primary_location:
                            source = primary_location.get('source', {})
                            venue = source.get('display_name')
                    else:
                        title = getattr(paper, 'title', None)
                        authors_list = getattr(paper, 'authorships', [])
                        year = getattr(paper, 'publication_year', None)
                        venue = None
                        if hasattr(paper, 'primary_location') and paper.primary_location:
                            if hasattr(paper.primary_location, 'source') and paper.primary_location.source:
                                venue = paper.primary_location.source.display_name
                    
                    authors = None
                    if authors_list:
                        if isinstance(paper, dict):
                            author_names = [a.get('author', {}).get('display_name', '') for a in authors_list[:3]]
                        else:
                            author_names = [a.author.display_name for a in authors_list[:3] if hasattr(a, 'author') and hasattr(a.author, 'display_name')]
                        author_names = [a for a in author_names if a]
                        if author_names:
                            authors = ', '.join(author_names)
                            if len(authors_list) > 3:
                                authors += ' et al.'

                    match_results.append(PDFMatchResult(
                        filename=filename,
                        metadata=PDFMetadata(
                            filename=filename,
                            title=title_orig,
                            authors=authors_orig,
                            year=year_orig,
                            doi=doi_orig,
                            venue=venue_orig
                        ),
                        matched=True,
                        paper_id=result.paper_id,
                        title=title,
                        authors=authors,
                        year=year,
                        venue=venue,
                        confidence=result.confidence,
                        match_method=result.match_method
                    ))
                    matched_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"Failed to extract metadata from paper {result.paper_id}: {e}")
                    match_results.append(PDFMatchResult(
                        filename=filename,
                        metadata=PDFMetadata(
                            filename=filename,
                            title=title_orig,
                            authors=authors_orig,
                            year=year_orig,
                            doi=doi_orig,
                            venue=venue_orig
                        ),
                        matched=False
                    ))
            else:
                match_results.append(PDFMatchResult(
                    filename=filename,
                    metadata=PDFMetadata(
                        filename=filename,
                        title=title_orig,
                        authors=authors_orig,
                        year=year_orig,
                        doi=doi_orig,
                        venue=venue_orig
                    ),
                    matched=False
                ))
        
        session.match_results = match_results
        self._store.save(session)
        
        self.logger.info(f"Matching complete: {matched_count}/{len(match_results)} matched")
        
        return PDFMatchResponse(
            upload_id=upload_id,
            results=match_results,
            matched_count=matched_count,
            unmatched_count=len(match_results) - matched_count
        )
    
    def get_matched_seeds(self, upload_id: str, action: str) -> List[Dict]:

        session = self._get_session(upload_id)
        
        if not session.match_results:
            raise InvalidInputException("No match results available. Please match metadata first.")
        
        if action == "skip_all":
            return []
        
        elif action == "use_all":
            seeds = []
            for result in session.match_results:
                if result.matched:
                    seeds.append({
                        "paper_id": result.paper_id,
                        "title": result.title,
                        "authors": result.authors,
                        "year": result.year,
                        "venue": result.venue,
                        "confidence": result.confidence,
                        "match_method": result.match_method,
                        "source_id": result.filename,
                    })
            return seeds
        
        else:
            raise InvalidInputException(f"Invalid action: {action}")
    
    def cleanup_session(self, upload_id: str):

        session = self._store.delete(upload_id)
        if not session:
            raise InvalidInputException(f"Upload session {upload_id} not found")

        self._storage.remove_dir(session.temp_dir)
        self.logger.info(f"Cleaned up uploaded files for {upload_id}")

    def get_reviewed_metadata(self, upload_id: str) -> List[PDFMetadata]:
        """Return reviewed metadata for a session."""
        session = self._get_session(upload_id)
        return session.reviewed_metadata

    def persist_source_files(self, upload_id: str, session_id: str, filenames: List[str]) -> Dict[str, str]:
        """Copy reviewed source files into persistent storage."""
        if not filenames or not self._source_file_service:
            return {}

        session = self._get_session(upload_id)
        stored: Dict[str, str] = {}

        for name in filenames:
            if not name:
                continue
            file_path = session.file_lookup.get(name)
            if not file_path:
                continue
            try:
                if not file_path.exists():
                    continue
            except OSError:
                continue
            file_id = self._source_file_service.persist_file(session_id, name, file_path)
            if file_id:
                stored[name] = file_id
        return stored
    
    def _get_session(self, upload_id: str) -> PDFUploadSession:
        """Get session or raise exception."""
        session = self._store.get(upload_id)
        if not session:
            raise InvalidInputException(f"Upload session {upload_id} not found")
        return session

    def _sanitize_filename(self, filename: Optional[str], temp_dir: Path) -> str:
        """Ensure uploaded files are saved with safe, unique filenames."""
        name = Path(filename or "").name
        if not name:
            name = "uploaded.pdf"
        stem = Path(name).stem or "uploaded"
        suffix = Path(name).suffix or ".pdf"
        candidate = f"{stem}{suffix}"
        counter = 1
        while (temp_dir / candidate).exists():
            candidate = f"{stem}_{counter}{suffix}"
            counter += 1
        return candidate

    def _requires_grobid(self, files: List[UploadFile]) -> bool:
        return any(self._is_pdf(f.filename) for f in files if f.filename)

    def _is_supported_file(self, filename: Optional[str]) -> bool:
        if not filename:
            return False
        return Path(filename).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _is_pdf(self, filename: Optional[str]) -> bool:
        if not filename:
            return False
        return Path(filename).suffix.lower() == ".pdf"

    def _to_schema_metadata(
        self,
        filename: str,
        metadata: Optional[ExtractedMetadata],
    ) -> PDFMetadata:
        if metadata is None:
            return PDFMetadata(filename=filename)
        
        authors_value = metadata.authors
        if isinstance(authors_value, list):
            authors_value = ", ".join(a.strip() for a in authors_value if a and a.strip())
        
        year_value = self._convert_year(metadata.year)
        
        return PDFMetadata(
            filename=filename,
            title=metadata.title,
            authors=authors_value or None,
            abstract=getattr(metadata, "abstract", None),
            year=year_value,
            doi=metadata.doi,
            venue=metadata.venue
        )

    def _convert_year(self, year_value: Optional[str]) -> Optional[int]:
        if not year_value:
            return None
        year_str = str(year_value)
        for token in year_str.split():
            if token.isdigit() and len(token) == 4:
                return int(token)
        digits = "".join(ch for ch in year_str if ch.isdigit())
        if len(digits) >= 4:
            return int(digits[:4])
        return None

    def _has_metadata(self, metadata: PDFMetadata) -> bool:
        return any([
            metadata.title,
            metadata.authors,
            metadata.abstract,
            metadata.year,
            metadata.doi,
            metadata.venue
        ])
