from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING
import logging

from ..library.library_manager import LibraryManager
from ..library.paper_file_reader import PaperFileReader
from ..library.models import LibraryConfig, PaperData, TopicCluster
from ..text_processing.topic_labeler import TopicLabeler
from ..library.topic_overview_writer import TopicOverviewWriter
from ..text_processing.preprocessing import TextPreProcessing
from ..text_processing.vectorization import TextTransformation
from ..text_processing.topic_modeling import TopicModeling
from ..config.text_config import TextProcessingConfig
from ..DataManagement.markdown_writer import MarkdownFileGenerator

if TYPE_CHECKING:
    from ..text_processing.topic_labeling_strategy import TopicLabelingStrategy


class TopicModelingOrchestrator:
    """
    Orchestrates topic modeling on a library.
    
    Responsibilities:
    - Load papers from library (delegates to PaperFileReader)
    - Coordinate topic modeling pipeline
    - Label topics (delegates to TopicLabeler)
    - Organize papers into topic folders
    
    Does NOT:
    - Run the actual topic modeling algorithm (delegates to TopicModeling)
    - Create the labels (delegates to TopicLabeler)
    - Parse files (delegates to PaperFileReader)
    - Handle CLI (delegates to CLI commands)
    """
    
    def __init__(
        self,
        library_manager: Optional[LibraryManager] = None,
        paper_reader: Optional[PaperFileReader] = None,
        topic_labeler: Optional[TopicLabeler] = None,
        topic_overview_writer: Optional[TopicOverviewWriter] = None,
        preprocessor: Optional[TextPreProcessing] = None,
        vectorizer: Optional[TextTransformation] = None,
        topic_model: Optional[TopicModeling] = None,
        topic_config: Optional[TextProcessingConfig] = None,
        labeling_strategy: Optional['TopicLabelingStrategy'] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize orchestrator with dependency injection.
        
        Args:
            library_manager: Library manager (creates if None)
            paper_reader: Paper file reader (creates if None)
            topic_labeler: Topic labeler (creates if None)
            preprocessor: Text preprocessor (creates if None)
            vectorizer: Text vectorizer (creates if None)
            topic_model: Topic modeling instance (creates if None)
            topic_config: Topic modeling configuration
            labeling_strategy: Strategy for labeling topics
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.topic_config = topic_config or TextProcessingConfig()
        
        self.library_manager = library_manager or LibraryManager(logger=self.logger)
        self.paper_reader = paper_reader or PaperFileReader(logger=self.logger)
        self.topic_labeler = topic_labeler or TopicLabeler(
            strategy=labeling_strategy, 
            logger=self.logger
        )
        self.topic_overview_writer = topic_overview_writer or TopicOverviewWriter()

        self.preprocessor = preprocessor or TextPreProcessing(self.topic_config)
        self.vectorizer = vectorizer or TextTransformation(self.topic_config)
        self.topic_model = topic_model or TopicModeling(self.topic_config)
    
    def run_topic_modeling(
    self,
    library_path: Path,
    model_type: str = 'NMF',
    num_topics: Optional[int] = None
) -> tuple[List[TopicCluster], Path]:
        """
        Run topic modeling on library and organize papers by topics.
        
        Args:
            library_path: Path to library
            model_type: Type of topic model ('NMF' or 'LDA')
            num_topics: Number of topics (overrides config)
            
        Returns:
            Tuple of (labeled_clusters, overview_path)  # UPDATE DOCSTRING
        """
        library_path = Path(library_path)
        
        if not self.library_manager.library_exists(library_path):
            raise FileNotFoundError(f"No library found at {library_path}")
        
        config = self.library_manager.load_library_config(library_path)
        self.logger.info(f"Running topic modeling on library: {config.name}")
        
        if num_topics:
            self.topic_config.num_topics = num_topics
        
        papers = self._load_papers_from_library(library_path)
        self.logger.info(f"Loaded {len(papers)} papers from library")
        
        if not papers:
            raise ValueError("No papers found in library")
        
        assignments, top_words = self._run_topic_modeling(papers, model_type)
        
        # Map assignments only to the papers that were actually modeled
        papers_with_abstracts = [p for p in papers if p.abstract]

        for i, paper in enumerate(papers_with_abstracts):
            paper.assigned_topic = int(assignments[i])

        # Assign a default topic (e.g., -1) to those without abstracts
        for paper in papers:
            if paper.abstract is None or not paper.abstract.strip():
                paper.assigned_topic = -1

        
        clusters = self._group_papers_by_cluster(papers)
        
        labeled_clusters = self.topic_labeler.label_clusters(
            clusters=clusters,
            top_words_per_cluster=top_words
        )
        
        label_map = {cluster.cluster_id: cluster.label for cluster in labeled_clusters}
        for paper in papers:
            paper.topic_label = label_map.get(paper.assigned_topic)
        
        self._organize_papers_by_topics(papers, labeled_clusters, library_path)
        
        # ADD THESE LINES - Create the overview file
        overview_path = self.topic_overview_writer.create_overview(
            clusters=labeled_clusters,
            library_path=library_path,
            model_type=model_type,
            num_topics=self.topic_config.num_topics
        )
        self.logger.info(f"Created topic overview at: {overview_path}")
        
        self.logger.info(f"Topic modeling complete. Created {len(labeled_clusters)} topic clusters")
        
        return labeled_clusters, overview_path  # CHANGE THIS LINE - was just: return labeled_clusters
    
    def _load_papers_from_library(self, library_path: Path) -> List[PaperData]:
        """
        Load all papers from library using PaperFileReader.
        
        Args:
            library_path: Library path
            
        Returns:
            List of PaperData objects
        """
        papers_dir = self.library_manager.get_papers_directory(library_path)
        
        papers = self.paper_reader.read_papers_from_directory(papers_dir)
        
        return papers
    
    def _run_topic_modeling(
        self,
        papers: List[PaperData],
        model_type: str
    ) -> tuple:
        """
        Run topic modeling on papers using injected components.
        
        Args:
            papers: List of papers
            model_type: Type of model ('NMF' or 'LDA')
            
        Returns:
            Tuple of (assignments, top_words_dict)
        """
        import pandas as pd
        
        papers_with_abstracts = [p for p in papers if p.abstract]
        
        if not papers_with_abstracts:
            raise ValueError("No papers with abstracts found for topic modeling")
        
        self.logger.info(
            f"Running {model_type} topic modeling on {len(papers_with_abstracts)} papers "
            f"with abstracts (out of {len(papers)} total)"
        )
        
        df_abstracts = pd.DataFrame({
            'paperId': [p.paper_id for p in papers_with_abstracts],
            'abstract': [p.abstract for p in papers_with_abstracts]
        })
        
        df_processed = self.preprocessor.process_abstracts(df_abstracts, logger=self.logger)
        
        df_final = self.preprocessor.filter_and_stem_abstracts_by_language(
            df_processed, 
            logger=self.logger
        )
        
        if df_final.empty:
            raise ValueError(
                f"No valid {self.topic_config.language} abstracts found after preprocessing"
            )
        
        self.logger.info(f"After preprocessing: {len(df_final)} valid abstracts")
        
        if model_type.upper() == 'NMF':
            self.vectorizer.vectorize_and_extract(
                df_final,
                model_type='TFIDF',
                logger=self.logger
            )
        else:
            self.vectorizer.vectorize_and_extract(
                df_final,
                model_type='COUNT',
                logger=self.logger
            )
        
        self.topic_model.apply_topic_modeling(
            transformation_instance=self.vectorizer,
            logger=self.logger,
            model_type=model_type
        )
        
        results = self.topic_model.results[model_type.upper()]
        assignments = results['assignments']
        top_words = results['top_words']
        
        return assignments, top_words
    
    def _group_papers_by_cluster(
        self,
        papers: List[PaperData]
    ) -> Dict[int, List[PaperData]]:
        """
        Group papers by assigned cluster.
        
        Args:
            papers: List of papers with assigned topics
            
        Returns:
            Dictionary mapping cluster_id to list of papers
        """
        clusters = {}
        
        for paper in papers:
            if paper.assigned_topic is not None:
                cluster_id = paper.assigned_topic
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(paper)
        
        return clusters
    
    def _organize_papers_by_topics(
        self,
        papers: List[PaperData],
        labeled_clusters: List[TopicCluster],
        library_path: Path
    ) -> None:
        """
        Organize papers into topic folders.
        
        Args:
            papers: List of papers with topic assignments
            labeled_clusters: List of labeled clusters
            library_path: Library path
        """
        self.logger.info("Organizing papers into topic folders")
        
        storage_config = self._create_storage_config(library_path)
        markdown_writer = MarkdownFileGenerator(
            storage_and_logging_options=storage_config,
            api_provider_type='openalex'
        )
        
        for cluster in labeled_clusters:
            topic_folder = self.library_manager.create_topic_folder(
                library_path=library_path,
                topic_label=cluster.label
            )
            
            self.logger.info(f"Created topic folder: {cluster.label}")
            
            cluster_papers = [p for p in papers if p.assigned_topic == cluster.cluster_id]
            
            for paper in cluster_papers:
                try:
                    safe_title = self._sanitize_filename(paper.title)
                    filename = f"{paper.paper_id}_{safe_title}.md"
                    output_path = topic_folder / filename
                    
                    markdown_writer.create_paper_markdown_with_openalex_metadata(
                        paper_data=paper,
                        output_path=output_path
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"Failed to save paper {paper.paper_id} to topic folder: {e}"
                    )
            
            self.logger.debug(f"Added {len(cluster_papers)} papers to topic '{cluster.label}'")
    
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