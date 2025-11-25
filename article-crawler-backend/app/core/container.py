from dependency_injector import containers, providers
import logging

from app.core.stores.seed_session_store import InMemorySeedSessionStore
from app.core.stores.pdf_upload_store import InMemoryPdfUploadStore
from app.core.stores.crawler_job_store import InMemoryCrawlerJobStore
from app.core.storage.file_storage import LocalTempFileStorage
from app.core.storage.persistent_file_storage import PersistentFileStorage
from app.core.executors.background import BackgroundJobExecutor
from app.services.author_topic_evolution_service import AuthorTopicEvolutionService
from app.services.configuration_service import ConfigurationService
from app.services.crawler_execution_service import CrawlerExecutionService
from app.services.integration_settings_service import IntegrationSettingsService
from app.services.keyword_service import KeywordService
from app.services.library_edit_service import LibraryEditService
from app.services.library_service import LibraryService
from app.services.pdf_seed_service import PDFSeedService
from app.services.seed_selection_service import SeedSelectionService
from app.services.seed_session_service import SeedSessionService
from app.services.source_file_service import SourceFileService
from app.services.staging_service import StagingService
from app.services.retraction_watch_service import RetractionWatchService
from app.services.topic_modeling_service import TopicModelingService
from app.services.zotero_seed_service import ZoteroSeedService
from app.core.config import settings
from app.services.manual_metadata_enricher import ManualMetadataEnricher
from app.services.staging_match_service import StagingMatchService
from app.services.staging_query_parser import StagingQueryParser
from app.services.pdf_seed_workflow_service import PDFSeedWorkflowService


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
    
    # Configuration
    config = providers.Configuration()
    
    # Logger
    logger = providers.Singleton(
        logging.getLogger,
        "ArticleCrawlerAPI"
    )
    
    # Shared Services
    seed_session_store = providers.Singleton(InMemorySeedSessionStore)

    pdf_upload_store = providers.Singleton(InMemoryPdfUploadStore)
    seed_selection_service = providers.Factory(SeedSelectionService, logger=logger)
    
    seed_session_service = providers.Singleton(
        SeedSessionService,
        logger=logger,
        store=seed_session_store
    )

    file_storage = providers.Singleton(LocalTempFileStorage)
    crawler_job_store = providers.Singleton(InMemoryCrawlerJobStore)
    job_executor = providers.Singleton(BackgroundJobExecutor, max_workers=2)

    staging_service = providers.Singleton(StagingService, logger=logger)
    staging_query_parser = providers.Singleton(StagingQueryParser)
    manual_metadata_enricher = providers.Factory(
        ManualMetadataEnricher,
        seed_selection_service=seed_selection_service,
    )
    staging_match_service = providers.Factory(
        StagingMatchService,
        seed_selection_service=seed_selection_service,
        logger=logger,
    )

    retraction_service = providers.Singleton(
        RetractionWatchService,
        logger=logger,
        staging_service=staging_service,
        cache_dir=settings.RETRACTION_CACHE_DIR,
    )

    staged_file_storage = providers.Singleton(
        PersistentFileStorage,
        base_dir=settings.STAGED_FILES_DIR,
        logger=logger,
    )

    source_file_service = providers.Singleton(
        SourceFileService,
        logger=logger,
        storage=staged_file_storage,
    )

    pdf_seed_service = providers.Singleton(
        PDFSeedService,
        logger=logger,
        upload_store=pdf_upload_store,
        file_storage=file_storage,
        source_file_service=source_file_service,
    )

    pdf_seed_workflow_service = providers.Factory(
        PDFSeedWorkflowService,
        pdf_seed_service=pdf_seed_service,
        staging_service=staging_service,
        seed_session_service=seed_session_service,
        logger=logger,
    )
    
    zotero_seed_service = providers.Singleton(ZoteroSeedService, logger=logger)

    keyword_service = providers.Singleton(KeywordService, logger=logger)

    configuration_service = providers.Singleton(ConfigurationService, logger=logger)

    integration_settings_service = providers.Singleton(
        IntegrationSettingsService,
        logger=logger
    )

    crawler_execution_service = providers.Singleton(
        CrawlerExecutionService,
        logger=logger,
        articlecrawler_path=config.provided.ARTICLECRAWLER_PATH,
        job_store=crawler_job_store,
        job_executor=job_executor,
    )

    library_service = providers.Singleton(LibraryService, logger=logger)

    library_edit_service = providers.Singleton(LibraryEditService, logger=logger)

    topic_modeling_service = providers.Singleton(TopicModelingService, logger=logger)

    author_topic_evolution_service = providers.Singleton(
        AuthorTopicEvolutionService,
        logger=logger
    )
