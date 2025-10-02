"""
Enhanced Crawler with dependency injection and service-oriented architecture.

The crawler now uses:
- API abstraction layer for interchangeable providers
- Service-oriented data management
- Focused configuration classes
- Strategy-based topic modeling
- Dependency injection throughout

All existing functionality is preserved while providing better maintainability
and extensibility through SOLID principles.
"""

from .api import create_api_provider
from .data import PaperRetrievalService, DataValidationService, DataCoordinator, FrameManager
from .config import (
    APIConfig, SamplingConfig, TextProcessingConfig, 
    StorageAndLoggingConfig, GraphConfig, RetractionConfig, StoppingConfig
)
from .text_processing import TextAnalysisManager
from .graph import GraphManager, GraphProcessing
from ArticleCrawler.LogManager.crawler_logger import CrawlerLogger
from ArticleCrawler.DataManagement.data_storage import DataStorage
from ArticleCrawler.sampling.sampler import Sampler
from ArticleCrawler.papervalidation.retraction_watch_manager import RetractionWatchManager
from contextlib import contextmanager

class Crawler:
    """
    Enhanced Crawler with dependency injection and SOLID architecture.
    
    This class maintains complete backward compatibility while using the new
    service-oriented architecture internally. All existing functionality
    is preserved while providing better separation of concerns.
    """
    
    def __init__(self, 
                 crawl_initial_condition, 
                 stopping_criteria_config,
                 api_config=None,
                 sampling_config=None,
                 text_config=None,
                 storage_config=None,
                 graph_config=None,
                 retraction_config=None,
                 # Backward compatibility parameters
                 reporting_options=None,
                 sampling_options=None,
                 nlp_options=None,
                 graph_options=None,
                 storage_and_logging_options=None,
                 retraction_options=None,
                 frames=None,
                 md_generator=None):
        """
        Initialize the Crawler with enhanced architecture.
        
        Args:
            crawl_initial_condition: Initial crawling parameters
            stopping_criteria_config: Stopping criteria configuration
            api_config: API provider configuration (new)
            sampling_config: Sampling configuration (new)
            text_config: Text processing configuration (new)
            storage_config: Storage and logging configuration (new)
            graph_config: Graph configuration (new)
            retraction_config: Retraction configuration (new)
            # Backward compatibility arguments
            reporting_options: Legacy reporting options
            sampling_options: Legacy sampling options (maps to sampling_config)
            nlp_options: Legacy NLP options (maps to text_config)
            graph_options: Legacy graph options (maps to graph_config)
            storage_and_logging_options: Legacy storage options (maps to storage_config)
            retraction_options: Legacy retraction options (maps to retraction_config)
            frames: Pre-existing frame manager
            md_generator: Markdown generator
        """
        
        # Handle backward compatibility by converting old options to new configs
        self._resolve_configurations(
            api_config, sampling_config, text_config, storage_config,
            graph_config, retraction_config, stopping_criteria_config,
            sampling_options, nlp_options, graph_options,
            storage_and_logging_options, retraction_options
        )
        
        # Store core parameters
        self.crawl_initial_condition = crawl_initial_condition
        self.crawl_initial_condition.validate_keywords()
        self.md_generator = md_generator

        self.logger = CrawlerLogger(self.storage_config)
        
        self.data_storage = DataStorage(
            storage_and_logging_options=self.storage_config,
            logger=self.logger
        )

        self._create_services()
        
        self.logger.info(f"Enhanced Crawler initialized with {self.api_config.provider_type} API provider")
        self.logger.info(f"Data coordinator seeded with paperIds {self.crawl_initial_condition.seed_paperid}")
        self.logger.log_reporting_information(data_manager=self.data_coordinator, iteration='Initialization')
        self.logger.info('Enhanced Crawler initialization finished.')

    def _resolve_configurations(self, api_config, sampling_config, text_config, storage_config,
                               graph_config, retraction_config, stopping_criteria_config,
                               sampling_options, nlp_options, graph_options,
                               storage_and_logging_options, retraction_options):
        """
        Resolve configuration objects, handling backward compatibility.
        
        This method ensures that both old-style options and new-style configs work.
        """
        self.api_config = api_config or APIConfig(
            provider_type='openalex',
            retries=3
        )
        
        if sampling_config:
            self.sampling_config = sampling_config
        elif sampling_options:
            # Convert old SamplingOptions to new SamplingConfig
            self.sampling_config = SamplingConfig(
                num_papers=sampling_options.num_papers,
                hyper_params=sampling_options.hyper_params,
                ignored_venues=sampling_options.ignored_venues,
                no_key_word_lambda=getattr(sampling_options, 'no_key_word_lmbda', 1.0)
            )
        else:
            self.sampling_config = SamplingConfig(num_papers=10)
        
        if text_config:
            self.text_config = text_config
        elif nlp_options:
            self.text_config = TextProcessingConfig(
                abstract_min_length=getattr(nlp_options, 'abstract_min_length', 120),
                language=getattr(nlp_options, 'language', 'en'),
                special_characters=getattr(nlp_options, 'special_characters', None),
                stopwords=getattr(nlp_options, 'stopwords', None),
                stemmer=getattr(nlp_options, 'stemmer', None),
                num_topics=getattr(nlp_options, 'num_topics', 20),
                default_topic_model_type=getattr(nlp_options, 'default_topic_model_type', 'NMF'),
                top_n_words_per_topic=getattr(nlp_options, 'top_n_words_per_topic', 10),
                random_state=getattr(nlp_options, 'random_state', 42),
                nmf_max_iter=getattr(nlp_options, 'nmf_max_iter', 1000),
                lda_max_iter=getattr(nlp_options, 'lda_max_iter', 10),
                lda_doc_topic_prior=getattr(nlp_options, 'lda_doc_topic_prior', 0.8),
                save_figures=getattr(nlp_options, 'save_figures', False),
                max_rows=getattr(nlp_options, 'max_rows', 4),
                max_columns=getattr(nlp_options, 'max_columns', 5)
            )
        else:
            self.text_config = TextProcessingConfig()
        
        if storage_config:
            self.storage_config = storage_config
        elif storage_and_logging_options:
            self.storage_config = storage_and_logging_options
        else:
            self.storage_config = StorageAndLoggingConfig()
        
        if graph_config:
            self.graph_config = graph_config
        elif graph_options:
            self.graph_config = GraphConfig(
                ignored_venues=getattr(graph_options, 'ignored_venues', []),
                include_author_nodes=getattr(graph_options, 'include_author_nodes', False)
            )
        else:
            self.graph_config = GraphConfig()
        
        if retraction_config:
            self.retraction_config = retraction_config
        elif retraction_options:
            self.retraction_config = RetractionConfig(
                enable_retraction_watch=getattr(retraction_options, 'enable_retraction_watch', True),
                avoid_retraction_in_sampler=getattr(retraction_options, 'avoid_retraction_in_sampler', False),
                avoid_retraction_in_reporting=getattr(retraction_options, 'avoid_retraction_in_reporting', True),
                retraction_watch_raw_url=getattr(retraction_options, 'retraction_watch_raw_url', 
                    "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv"),
                retraction_watch_commits_api_url=getattr(retraction_options, 'retraction_watch_commits_api_url',
                    "https://gitlab.com/api/v4/projects/crossref%2Fretraction-watch-data/repository/commits?path=retraction_watch.csv&per_page=1")
            )
        else:
            self.retraction_config = RetractionConfig()
        
        if isinstance(stopping_criteria_config, StoppingConfig):
            self.stopping_config = stopping_criteria_config
        else:
            self.stopping_config = StoppingConfig(
                max_iter=getattr(stopping_criteria_config, 'max_iter', 1),
                max_df_size=getattr(stopping_criteria_config, 'max_df_size', 1E9)
            )

    def _create_services(self):
        """
        Create all services using dependency injection.
        
        This method creates the service instances and wires them together
        using the configuration objects.
        """
        api_provider = create_api_provider(
            self.api_config.provider_type,
            **self.api_config.get_provider_kwargs(),
            logger=self.logger
        )
        
        self.retrieval_service = PaperRetrievalService(api_provider, self.logger)
        self.validation_service = DataValidationService(self.logger)
        
        self.frame_manager = FrameManager(
            reporting_options=None,
            data_storage_options=self.storage_config,
            logger=self.logger
        )
        
        self.retraction_manager = RetractionWatchManager(
            storage_and_logging_options=self.storage_config,
            retraction_options=self.retraction_config,
            logger=self.logger
        )
        
        self.graph_manager = GraphManager(
            reporting_options=None,
            graph_options=self.graph_config,
            logger=self.logger
        )
        
        
        self.data_coordinator = DataCoordinator(
            retrieval_service=self.retrieval_service,
            validation_service=self.validation_service,
            frame_manager=self.frame_manager,
            retraction_manager=self.retraction_manager,
            graph_manager=self.graph_manager,
            graph_processing=None,
            crawl_initial_condition=self.crawl_initial_condition,
            logger=self.logger
        )
        
        self.graph_processing = GraphProcessing(data_manager=self.data_coordinator, logger=self.logger)
        self.data_coordinator.graph_processing = self.graph_processing
        
        self.text_processor = TextAnalysisManager(
            config=self.text_config,
            retraction_watch_manager=self.retraction_manager
        )
        
        self.sampler = Sampler(
            keywords=self.crawl_initial_condition.keywords,
            data_manager=self.data_coordinator,
            sampling_options=self.sampling_config,
            logger=self.logger,
            data_storage_options=self.storage_config,
            retraction_watch_manager=self.retraction_manager
        )

    def crawl(self):
        """
        Enhanced crawl method using the new architecture.
        
        This method maintains the exact same behavior as the original
        but uses the new service-oriented architecture internally.
        """
        self.logger.info(f"Keywords and expressions to filter titles {self.crawl_initial_condition.keywords}")
        self.logger.info(f"Using {self.api_config.provider_type} API provider for crawling")

        iteration = 0
        self.logger.info('Enhanced crawling started with dependency injection architecture.')

        while self._should_continue_crawling(iteration):
            self.logger.set_iteration(iteration)
            self.logger.info(f'Starting iteration {iteration} with enhanced architecture')

            self.logger.info('Sampling started with enhanced service architecture.')
            self.sampler.sample_papers()
            selected_paperIds = self.sampler.sampled_papers
            
            if selected_paperIds is not None and len(selected_paperIds) > 0:
                if hasattr(selected_paperIds, 'tolist'):
                    paper_ids = selected_paperIds.tolist()
                else:
                    paper_ids = list(selected_paperIds)
                
                self.logger.info('Retrieving and processing papers using enhanced DataCoordinator.')
                
                self.data_coordinator.retrieve_and_process_papers(paper_ids, paperIDs_are_sampled=True)

                if self.data_coordinator.no_papers_retrieved:
                    self.logger.info('No papers retrieved after API call. Stopping the crawl')
                else:
                    self.logger.info('Papers retrieved and processed successfully with enhanced architecture.')

                self.logger.info('Saving intermediate files.')
                self.data_storage.save_intermediate_file(self, iteration)
            else:
                self.sampler.no_papers_available = True
                self.logger.info('No papers returned by the enhanced sampler. Stopping.')

            self.logger.log_reporting_information(data_manager=self.data_coordinator, iteration=iteration)
            self.logger.info('Enhanced iteration %d completed.', iteration)

            iteration += 1

        self._finalize_crawling()

    def _should_continue_crawling(self, iteration):
        """
        Enhanced stopping condition check using new configuration.
        
        Args:
            iteration: Current iteration number
            
        Returns:
            bool: True if crawling should continue
        """
        continue_crawl = True

        if iteration >= self.stopping_config.max_iter:
            continue_crawl = False
            self.logger.info("Stopping condition reached: Maximum iteration limit exceeded.")

        if self.data_coordinator.frames.df_paper_metadata.shape[0] >= self.stopping_config.max_df_size:
            continue_crawl = False
            self.logger.info("Stopping condition reached: Maximum DataFrame size exceeded.")

        if iteration > 0 and self.sampler.no_papers_available:
            continue_crawl = False
            self.logger.info("Stopping condition reached: No suitable papers available for crawling.")

        if iteration > 0 and self.data_coordinator.no_papers_retrieved:
            continue_crawl = False
            self.logger.info("Stopping condition reached: No papers retrieved.")

        if continue_crawl:
            self.logger.info(f"Stopping condition not reached. Continuing enhanced crawl. Iteration {iteration}")

        return continue_crawl

    def _finalize_crawling(self):
        """Finalize the crawling process."""
        # Move final file
        experiment_file_name = self.storage_config.experiment_file_name
        filepath_final_pkl, timestamp_final_pkl = self.data_storage.save_final_file(self, experiment_file_name)
        self.storage_config.filepath_final_pkl = filepath_final_pkl
        self.storage_config.timestamp_final_pkl = timestamp_final_pkl
        
        self.logger.info('Enhanced Crawler finished successfully.')
        self.data_coordinator.check_and_log_inconsistent_papers()
        self.logger.shutdown()

    def generate_markdown_files(self):
        """Generate markdown files using the enhanced data coordinator."""
        if self.md_generator:
            self.md_generator.generate_markdown_files_from_crawler(self.data_coordinator)
        else:
            self.logger.warning("No markdown generator provided")

    def analyze_and_report(self, **kwargs):
        """
        Enhanced analysis and reporting using strategy-based text processing.
        
        This method uses the new text processing architecture with strategy-based
        topic modeling while maintaining backward compatibility.
        """
        self.logger.info("Starting enhanced analysis and report generation with strategy-based architecture.")
        
        try:
            with temporary_text_config(self.text_config, **kwargs) as modified_config:
                self.text_processor.config = modified_config
                
                self.text_processor.analyze_and_report(
                    data_manager=self.data_coordinator,
                    logger=self.logger,
                    figure_folder=self.storage_config.figure_folder,
                    timestamp_final_pkl=self.storage_config.timestamp_final_pkl,
                    experiment_file_name=self.storage_config.experiment_file_name,
                    xlsx_folder=self.storage_config.xlsx_folder,
                    vault_folder=self.storage_config.vault_folder,
                    config=modified_config
                )
                
                self.logger.info(f"PKL file stored at {self.storage_config.filepath_final_pkl}")

        except Exception as e:
            self.logger.error(f"An error occurred during enhanced analysis and report generation: {e}")
            raise

    # Backward compatibility properties
    @property
    def data_manager(self):
        """Backward compatibility: provide access to data_coordinator as data_manager."""
        return self.data_coordinator
    
    @property
    def stopping_criteria_options(self):
        """Backward compatibility: provide access to stopping configuration."""
        return self.stopping_config
    
    @property 
    def reporting_options(self):
        """Backward compatibility: legacy reporting options."""
        return None
    
    @property
    def sampling_options(self):
        """Backward compatibility: provide access to sampling configuration."""
        return self.sampling_config
        
    @property
    def nlp_options(self):
        """Backward compatibility: provide access to text configuration."""
        return self.text_config
    
    @property
    def graph_options(self):
        """Backward compatibility: provide access to graph configuration."""
        return self.graph_config
        
    @property
    def storage_and_logging_options(self):
        """Backward compatibility: provide access to storage configuration."""
        return self.storage_config
    
    @property
    def retraction_options(self):
        """Backward compatibility: provide access to retraction configuration."""
        return self.retraction_config


@contextmanager
def temporary_text_config(text_config, **kwargs):
    """
    Context manager for temporarily modifying text configuration.
    
    Args:
        text_config: Original text configuration
        **kwargs: Temporary modifications
        
    Yields:
        Modified configuration copy
    """
    modified_config = text_config.copy()

    for key, value in kwargs.items():
        if hasattr(modified_config, key):
            setattr(modified_config, key, value)
        else:
            print(f"Warning: Unknown text configuration attribute: {key}")

    try:
        yield modified_config
    finally:
        pass