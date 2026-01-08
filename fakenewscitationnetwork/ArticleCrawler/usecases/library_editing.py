"""
Library Editing Orchestrator

Responsibilities:
- Add papers (by paper_id) to an existing library
- Remove papers (by paper_id) from an existing library
- List papers in a library

Delegates to:
- API provider for fetching PaperData
- LibraryManager for filesystem structure/helpers
- MarkdownFileGenerator for writing files

Design:
- Reuse LibraryCreationOrchestrator internals to avoid duplication when saving papers
"""

from pathlib import Path
from typing import List, Optional, Dict
import logging

from ..library.library_manager import LibraryManager
from ..library.paper_file_reader import PaperFileReader
from ..library.models import PaperData
from ..api import create_api_provider


class LibraryEditOrchestrator:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.library_manager = LibraryManager(logger=self.logger)

    def _resolve_api_provider(self, library_path: Path, override: Optional[str] = None):
        if override:
            return create_api_provider(override, logger=self.logger), override
        # Use library-config api_provider if available
        try:
            config = self.library_manager.load_library_config(library_path)
            provider = getattr(config, 'api_provider', 'openalex') or 'openalex'
            return create_api_provider(provider, logger=self.logger), provider
        except Exception:
            return create_api_provider('openalex', logger=self.logger), 'openalex'

    def list_papers(self, library_path: Path) -> List[PaperData]:
        reader = PaperFileReader(logger=self.logger)
        papers_dir = self.library_manager.get_papers_directory(library_path)
        return reader.read_papers_from_directory(papers_dir)

    def add_papers(self, library_path: Path, paper_ids: List[str], api_provider: Optional[str] = None) -> Dict:
        """
        Add papers to an existing library. Skips papers that already exist.
        Returns dict with counts and list of added paper_ids.
        """
        library_path = Path(library_path)
        if not self.library_manager.library_exists(library_path):
            raise FileNotFoundError(f"No library found at {library_path}")

        api, resolved_provider = self._resolve_api_provider(library_path, api_provider)

        # Prepare writer
        from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
        storage_config = self._create_storage_config(library_path)
        md_writer = MarkdownFileGenerator(
            storage_and_logging_options=storage_config,
            api_provider_type=resolved_provider
        )

        papers_dir = self.library_manager.get_papers_directory(library_path)
        added = []
        skipped_existing = []
        failed = []

        for pid in paper_ids:
            try:
                # Skip if a file with this prefix already exists
                existing = list(papers_dir.glob(f"{pid}_*.md"))
                if existing:
                    skipped_existing.append(pid)
                    continue

                paper_data = api.get_paper_as_paper_data(pid)
                if not paper_data:
                    failed.append(pid)
                    continue

                safe_title = self.library_manager.sanitize_filename(paper_data.title)
                filename = f"{paper_data.paper_id}_{safe_title}.md"
                output_path = papers_dir / filename
                md_writer.create_paper_markdown_with_openalex_metadata(
                    paper_data=paper_data,
                    output_path=output_path
                )
                added.append(pid)
            except Exception as e:
                self.logger.error(f"Failed adding {pid}: {e}")
                failed.append(pid)

        return {
            'api_provider': resolved_provider,
            'requested': len(paper_ids),
            'added_count': len(added),
            'skipped_existing': skipped_existing,
            'failed': failed,
            'added_ids': added,
        }

    def remove_papers(self, library_path: Path, paper_ids: List[str]) -> Dict:
        """
        Remove papers from a library by ID. Deletes files in papers/ and any topic folders.
        Returns dict with removed/skipped counts.
        """
        library_path = Path(library_path)
        if not self.library_manager.library_exists(library_path):
            raise FileNotFoundError(f"No library found at {library_path}")

        removed = []
        not_found = []

        papers_dir = self.library_manager.get_papers_directory(library_path)
        topics_dir = self.library_manager.get_topics_directory(library_path)

        for pid in paper_ids:
            found_any = False
            # In main papers folder
            for file in papers_dir.glob(f"{pid}_*.md"):
                try:
                    file.unlink(missing_ok=True)
                    found_any = True
                except Exception as e:
                    self.logger.warning(f"Failed to delete {file}: {e}")
            # In topic folders (if exist)
            if topics_dir.exists():
                for topic_sub in topics_dir.glob("*/"):
                    for file in Path(topic_sub).glob(f"{pid}_*.md"):
                        try:
                            file.unlink(missing_ok=True)
                            found_any = True
                        except Exception as e:
                            self.logger.warning(f"Failed to delete {file}: {e}")

            if found_any:
                removed.append(pid)
            else:
                not_found.append(pid)

        return {
            'requested': len(paper_ids),
            'removed_count': len(removed),
            'not_found': not_found,
            'removed_ids': removed,
        }

    def _create_storage_config(self, library_path: Path):
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

