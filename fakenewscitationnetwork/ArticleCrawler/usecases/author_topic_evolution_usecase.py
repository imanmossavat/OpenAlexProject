
from pathlib import Path
from typing import Optional, List
import logging
import shutil

from ArticleCrawler.library.models import (
    AuthorInfo,
    PaperData,
    AuthorTopicEvolutionResult
)
from ArticleCrawler.library.author_search_service import AuthorSearchService
from ArticleCrawler.library.library_manager import LibraryManager
from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
from ArticleCrawler.usecases.topic_modeling_usecase import TopicModelingOrchestrator
from ArticleCrawler.library.temporal_analysis_service import TemporalAnalysisService
from ArticleCrawler.visualization.topic_evolution_visualizer import TopicEvolutionVisualizer
from ArticleCrawler.utils.library_temp_manager import TempLibraryManager
from ArticleCrawler.config.text_config import TextProcessingConfig
from ArticleCrawler.config.temporal_config import TemporalAnalysisConfig
from ArticleCrawler.visualization.visualization_config import VisualizationConfig
from ArticleCrawler.api.base_api import BaseAPIProvider

class AuthorTopicEvolutionUseCase:
    """
    Orchestrates the complete author topic evolution analysis workflow.
    
    This use case:
    1. Searches for and selects an author
    2. Retrieves the author's papers
    3. Creates a library (temporary or permanent)
    4. Runs topic modeling on papers
    5. Performs temporal analysis
    6. Generates visualizations
    """
    
    def __init__(
        self,
        api_provider: BaseAPIProvider,
        author_search_service: AuthorSearchService,
        library_manager: LibraryManager,
        topic_orchestrator: TopicModelingOrchestrator,
        temporal_analyzer: TemporalAnalysisService,
        visualizer: TopicEvolutionVisualizer,
        temp_library_manager: TempLibraryManager,
        markdown_writer: MarkdownFileGenerator,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize use case with all dependencies.
        
        Args:
            api_provider: API provider for fetching papers
            author_search_service: Service for author search
            library_manager: Manager for library operations
            topic_orchestrator: Orchestrator for topic modeling
            temporal_analyzer: Service for temporal analysis
            visualizer: Visualizer for topic evolution
            temp_library_manager: Manager for temporary libraries
            markdown_writer: Writer for markdown files
            logger: Logger instance
        """
        self.api_provider = api_provider
        self.author_search_service = author_search_service
        self.library_manager = library_manager
        self.topic_orchestrator = topic_orchestrator
        self.temporal_analyzer = temporal_analyzer
        self.visualizer = visualizer
        self.temp_library_manager = temp_library_manager
        self.markdown_writer = markdown_writer
        self.logger = logger or logging.getLogger(__name__)
    
    def run(
        self,
        author: AuthorInfo,
        model_type: str = 'NMF',
        num_topics: int = 5,
        save_library: bool = False,
        library_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
        max_papers: Optional[int] = None
    ) -> AuthorTopicEvolutionResult:
        """
        Run complete author topic evolution analysis.
        
        Args:
            author: Author information
            model_type: Topic modeling algorithm ('NMF' or 'LDA')
            num_topics: Number of topics to extract
            save_library: Whether to save library permanently
            library_path: Path for permanent library (if save_library=True)
            output_path: Optional path to copy final visualization
            max_papers: Optional limit on number of papers to analyze
            
        Returns:
            AuthorTopicEvolutionResult with analysis results
            
        Raises:
            ValueError: If insufficient papers or invalid configuration
        """
        self.logger.info(f"Starting topic evolution analysis for author: {author.name}")
        
        papers = self._fetch_author_papers(author, max_papers)
        
        if save_library and library_path:
            lib_path = self._create_permanent_library(author, papers, library_path)
            is_temporary = False
        else:
            lib_path = self._create_temp_library(author, papers)
            is_temporary = True
        
        self._run_topic_modeling(lib_path, model_type, num_topics)
        
        papers_with_topics = self._reload_papers_with_topics(lib_path)
        
        temporal_data = self.temporal_analyzer.analyze_evolution(author, papers_with_topics)
        
        viz_path = lib_path / "topic_evolution.png"
        self.visualizer.visualize(temporal_data, viz_path)
        
        final_viz_path = viz_path
        if output_path:
            final_viz_path = self._copy_visualization(viz_path, output_path)
        
        result = AuthorTopicEvolutionResult(
            author=author,
            temporal_data=temporal_data,
            visualization_path=final_viz_path,
            library_path=lib_path if save_library else None,
            is_temporary=is_temporary,
            model_type=model_type,
            num_topics=num_topics,
            time_period_years=self.temporal_analyzer.config.time_period_years
        )
        
        self.logger.info("Author topic evolution analysis complete")
        return result
    
    def _fetch_author_papers(
        self, 
        author: AuthorInfo,
        max_papers: Optional[int]
    ) -> List[PaperData]:
        """Fetch all papers by author with full metadata."""
        self.logger.info(f"Fetching papers for author: {author.name} ({author.id})")
        
        papers = self.api_provider.get_author_papers_as_paper_data(
            author.id,
            max_papers=max_papers
        )
        
        if not papers:
            raise ValueError(f"No papers found for author {author.name}")
        
        self.logger.info(f"Retrieved {len(papers)} papers")
        return papers
    
    def _create_temp_library(
        self, 
        author: AuthorInfo, 
        papers: List[PaperData]
    ) -> Path:
        """Create a temporary library for the author."""
        self.logger.info("Creating temporary library")
        
        safe_name = author.name.replace(" ", "_").lower()
        lib_path = self.temp_library_manager.create_temp_library(
            prefix=f"author_{safe_name}_"
        )
        
        library_name = f"{author.name} - Topic Evolution"
        self.library_manager.create_library_structure(lib_path, library_name)        
        
        from ArticleCrawler.library.models import LibraryConfig
        config = LibraryConfig(
            name=f"{author.name} - Topic Evolution",
            base_path=lib_path,
            description=f"Temporary library for topic evolution analysis of {author.name}",
            api_provider='openalex'
        )
        self.library_manager.save_library_config(config)
        
        self._save_papers_to_library(lib_path, papers)
        
        return lib_path
    
    def _create_permanent_library(self,author: AuthorInfo,papers: List[PaperData],library_path: Path) -> Path:
        """Create a permanent library for the author."""
        self.logger.info(f"Creating permanent library at: {library_path}")
        
        if library_path.exists():
            config_file = library_path / "library_config.yaml"
            if config_file.exists():
                self.logger.warning(f"Library already exists at: {library_path}")
                self.logger.info("Using existing library")
                return library_path
            else:
                self.logger.warning(f"Directory exists but is not a library: {library_path}")
                raise FileExistsError(
                    f"Directory already exists at: {library_path} "
                    "Please choose a different path or delete the directory."
                )
        
        library_name = f"{author.name} - Research Topics"
        library_path.mkdir(parents=True, exist_ok=True)
        self.library_manager.create_library_structure(library_path, library_name)
        
        from ArticleCrawler.library.models import LibraryConfig
        config = LibraryConfig(
            name=library_name,
            base_path=library_path,
            description=f"Research papers and topic analysis for {author.name}",
            api_provider='openalex'
        )
        self.library_manager.save_library_config(config)
        
        self._save_papers_to_library(library_path, papers)
        
        return library_path
    
    def _save_papers_to_library(self, library_path: Path, papers: List[PaperData]):
        """Save papers as markdown files in library."""
        papers_dir = self.library_manager.get_papers_directory(library_path)
        
        self.logger.info(f"Saving {len(papers)} papers to library")
        
        storage_config = self._create_storage_config(library_path)
        markdown_writer = MarkdownFileGenerator(
            storage_and_logging_options=storage_config,
            api_provider_type='openalex'
        )
        
        for paper in papers:
            try:
                safe_title = self.library_manager.sanitize_filename(paper.title)
                filename = f"{paper.paper_id}_{safe_title}.md"
                output_path = papers_dir / filename
                
                markdown_writer.create_paper_markdown_with_openalex_metadata(
                    paper_data=paper,
                    output_path=output_path
                )
                
            except Exception as e:
                self.logger.error(f"Failed to save paper {paper.paper_id}: {e}")
        
        self.logger.info(f"Saved {len(papers)} papers to {papers_dir}")


    def _create_storage_config(self, library_path: Path):
        """Create minimal storage config for MarkdownFileGenerator."""
        class SimpleStorageConfig:
            def __init__(self, lib_path):
                self.experiment_file_name = 'library'
                self.vault_folder = lib_path
                self.abstracts_folder = lib_path / 'papers'
                self.figure_folder = lib_path / 'figures'
                self.metadata_folder = lib_path / 'metadata'
                self.summary_folder = lib_path / 'summary'
                self.open_vault_folder = False
        
        return SimpleStorageConfig(library_path)

    
    def _run_topic_modeling(
        self,
        library_path: Path,
        model_type: str,
        num_topics: int
    ):
        """Run topic modeling on library."""
        self.logger.info(f"Running {model_type} topic modeling with {num_topics} topics")
        
        self.topic_orchestrator.run_topic_modeling(
            library_path=library_path,
            model_type=model_type,
            num_topics=num_topics
        )
        
        self.logger.info("Topic modeling complete")
    
    def _reload_papers_with_topics(self, library_path: Path) -> List[PaperData]:
        """Reload papers from library with topic assignments."""
        from ArticleCrawler.library.paper_file_reader import PaperFileReader
        
        papers_dir = self.library_manager.get_papers_directory(library_path)
        reader = PaperFileReader(logger=self.logger)
        
        papers = reader.read_papers_from_directory(papers_dir)
        
        papers_with_topics = [p for p in papers if p.topic_label is not None]
        
        self.logger.info(f"Reloaded {len(papers_with_topics)} papers with topic assignments")
        return papers_with_topics
    
    def _copy_visualization(self, source: Path, destination: Path) -> Path:
        """Copy visualization to specified output path."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, destination)
        self.logger.info(f"Copied visualization to: {destination}")
        return destination