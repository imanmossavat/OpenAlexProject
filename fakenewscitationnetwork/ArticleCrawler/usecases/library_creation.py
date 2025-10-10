"""
Library Creation Use Case Orchestrator - REFACTORED
Single Responsibility: Coordinate library creation from various sources.
"""

from pathlib import Path
from typing import List, Optional
import logging

from ..library.library_manager import LibraryManager
from ..library.models import LibraryConfig, PaperData
from ..DataManagement.markdown_writer import MarkdownFileGenerator
from ..api import create_api_provider


class LibraryCreationOrchestrator:
    """
    Orchestrates library creation workflow.
    
    Responsibilities:
    - Coordinate library creation process
    - Fetch papers via API (delegates to API provider)
    - Save papers (delegates to MarkdownFileGenerator)
    
    Does NOT:
    - Transform API responses (API provider does this now)
    - Parse files (PaperFileReader does this)
    - Handle CLI (CLI commands do this)
    """
    
    def __init__(
        self,
        api_provider: str = 'openalex',
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            api_provider: API provider to use
            logger: Optional logger instance
        """
        self.api_provider = api_provider
        self.logger = logger or logging.getLogger(__name__)
        self.library_manager = LibraryManager(logger=self.logger)
        self.api = create_api_provider(api_provider, logger=self.logger)
    
    def create_library(
        self,
        library_name: str,
        library_path: Path,
        paper_ids: List[str],
        description: Optional[str] = None
    ) -> LibraryConfig:
        """
        Create library from paper IDs.
        
        Args:
            library_name: Name for the library
            library_path: Path where to create library
            paper_ids: List of paper IDs (already matched)
            description: Optional library description
            
        Returns:
            Created library configuration
        """
        self.logger.info(f"Creating library '{library_name}' with {len(paper_ids)} papers")
        
        self.library_manager.create_library_structure(library_path, library_name)
        
        config = LibraryConfig(
            name=library_name,
            base_path=library_path,
            description=description,
            api_provider=self.api_provider
        )
        self.library_manager.save_library_config(config)
        
        papers_saved = self._fetch_and_save_papers(paper_ids, library_path)
        
        self.logger.info(
            f"Library created successfully at {library_path}. "
            f"Saved {papers_saved}/{len(paper_ids)} papers"
        )
        
        return config
    
    def _fetch_and_save_papers(
        self,
        paper_ids: List[str],
        library_path: Path
    ) -> int:
        """
        Fetch papers and save to library.
        
        Args:
            paper_ids: List of paper IDs
            library_path: Library path
            
        Returns:
            Number of papers successfully saved
        """
        papers_dir = self.library_manager.get_papers_directory(library_path)
        saved_count = 0
        
        storage_config = self._create_storage_config(library_path)
        markdown_writer = MarkdownFileGenerator(
            storage_and_logging_options=storage_config,
            api_provider_type=self.api_provider
        )
        
        for i, paper_id in enumerate(paper_ids, 1):
            try:
                self.logger.info(f"Fetching paper {i}/{len(paper_ids)}: {paper_id}")
                
                paper_data = self.api.get_paper_as_paper_data(paper_id)
                
                if paper_data:
                    safe_title = self._sanitize_filename(paper_data.title)
                    filename = f"{paper_data.paper_id}_{safe_title}.md"
                    output_path = papers_dir / filename
                    
                    markdown_writer.create_paper_markdown_with_openalex_metadata(
                        paper_data=paper_data,
                        output_path=output_path
                    )
                    
                    saved_count += 1
                    self.logger.debug(f"Saved paper: {filename}")
                else:
                    self.logger.warning(f"No data returned for paper {paper_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to process paper {paper_id}: {e}")
                continue
        
        return saved_count
    
    def _create_storage_config(self, library_path: Path):
        """
        Create minimal storage config for markdown writer.
        
        Args:
            library_path: Library path
            
        Returns:
            Simple object with required attributes
        """
        class SimpleStorageConfig:
            def __init__(self, library_path):
                self.experiment_file_name = 'library'
                self.vault_folder = library_path
                self.abstracts_folder = library_path / 'papers'
                self.figure_folder = library_path / 'figures'
                self.metadata_folder = library_path / 'metadata'
                self.summary_folder = library_path / 'summary'
                self.open_vault_folder = False
        
        return SimpleStorageConfig(library_path)
    
    def _sanitize_filename(self, title: str, max_length: int = 50) -> str:
        """
        Create safe filename from title.
        
        Args:
            title: Paper title
            max_length: Maximum length
            
        Returns:
            Sanitized filename
        """
        safe = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        safe = safe.replace(' ', '_')
        return safe[:max_length]