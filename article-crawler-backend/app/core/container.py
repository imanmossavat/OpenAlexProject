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
from app.services.crawler import (
    CrawlerConfigBuilder,
    CrawlerJobRunner,
    CrawlerResultAssembler,
)
from app.services.crawler_execution_service import CrawlerExecutionService
from app.services.catalog import (
    CatalogLazyFrameBuilder,
    ColumnOptionsBuilder,
    PaperCatalogExporter,
)
from app.services.workflows.pdf_helpers import (
    PDFSeedEnricher,
    PDFMatchedSeedBuilder,
    PDFStagingRowBuilder,
)
from app.services.staging.session_store import StagingSessionStore
from app.services.staging.query_utils import StagingQueryHelper
from app.services.staging.repository import StagingRepository
from app.services.staging.query_service import StagingQueryService
from app.services.staging.retraction_updater import StagingRetractionUpdater
from app.services.staging.row_manager import StagingRowManager
from app.services.integration_settings_service import IntegrationSettingsService
from app.services.keyword.service import KeywordService
from app.services.library.edit_service import LibraryEditService
from app.services.library.service import LibraryService
from app.services.pdf.service import PDFSeedService
from app.services.pdf.adapters import (
    GrobidManagerAdapter,
    MetadataExtractionAdapter,
    PDFMetadataMatcherAdapter,
    PDFMatchResultBuilder,
)
from app.services.seeds.selection_service import SeedSelectionService
from app.services.seeds.session_service import SeedSessionService
from app.services.source_file_service import SourceFileService
from app.services.staging.service import StagingService
from app.services.retraction.watch_service import RetractionWatchService
from app.services.topics.service import TopicModelingService
from app.services.zotero.service import ZoteroSeedService
from app.core.config import settings
from app.services.manual_metadata.helpers import (
    ManualMetadataLookup,
    ManualMetadataMerger,
    ManualMetadataRepository,
)
from app.services.manual_metadata.enricher import ManualMetadataEnricher
from app.services.staging.match_service import StagingMatchService
from app.services.staging.matchers import APIMetadataMatcherFactory
from app.services.staging.query_parser import StagingQueryParser
from app.services.pdf.workflow_service import PDFSeedWorkflowService
from app.services.paper_metadata_service import PaperMetadataService
from app.repositories import (
    PaperCatalogRepository,
    PaperAnnotationRepository,
)
from app.services.catalog.service import PaperCatalogService
from app.services.retraction.helpers import (
    RetractionCacheRepository,
    RetractionDOINormalizer,
    RetractionMetadataBuilder,
)
from app.services.library.helpers import (
    LibraryDetailsStore,
    LibraryMetadataFormatter,
    LibraryPathResolver,
    LibraryWorkflowRunner,
)
from app.services.settings.helpers import (
    IntegrationSettingsRepository,
    IntegrationSettingsValidator,
)
from app.services.keyword.helpers import KeywordRepository, KeywordFilterBuilder
from app.services.topics.helpers import (
    TopicModelingConfigBuilder,
    TopicResultRepository,
    TopicLabelBuilder,
    TopicResultFormatter,
)
from app.services.source_files.helpers import SourceFileRepository, SourceFileValidator
from app.services.seeds.helpers import (
    SeedAggregationHelper,
    SeedMatchBuilder,
    SeedMatchClientFactory,
    SeedResultBuilder,
    PaperMetadataFetcher,
    SeedSessionManager,
)
from app.services.providers.article_crawler import ArticleCrawlerAPIProviderFactory
from app.services.zotero.helpers import (
    ZoteroClientAdapter,
    ZoteroMetadataExtractorAdapter,
    ZoteroMatcherAdapter,
    ZoteroSessionStore,
    ZoteroMatchResultBuilder,
    ZoteroSeedEnricher,
)
from app.api.routes_helpers.library import LibraryRouteHelper
from app.api.routes_helpers.staging import StagingRouteHelper
from app.api.routes_helpers.seeds import SeedRouteHelper


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
    seed_session_manager = providers.Singleton(SeedSessionManager)

    pdf_upload_store = providers.Singleton(InMemoryPdfUploadStore)

    seed_match_client_factory = providers.Singleton(SeedMatchClientFactory, logger=logger)
    paper_metadata_fetcher = providers.Singleton(
        PaperMetadataFetcher,
        client_factory=seed_match_client_factory,
        logger=logger,
    )
    seed_match_builder = providers.Singleton(SeedMatchBuilder, logger=logger)
    seed_result_builder = providers.Singleton(
        SeedResultBuilder,
        match_builder=seed_match_builder,
        logger=logger,
    )
    seed_aggregation_helper = providers.Singleton(SeedAggregationHelper)

    seed_selection_service = providers.Factory(
        SeedSelectionService,
        logger=logger,
        client_factory=seed_match_client_factory,
        metadata_fetcher=paper_metadata_fetcher,
        match_builder=seed_match_builder,
        result_builder=seed_result_builder,
        aggregator=seed_aggregation_helper,
    )

    seed_session_service = providers.Singleton(
        SeedSessionService,
        logger=logger,
        store=seed_session_store,
        session_manager=seed_session_manager,
    )

    article_api_factory = providers.Singleton(
        ArticleCrawlerAPIProviderFactory,
        logger=logger,
    )

    file_storage = providers.Singleton(LocalTempFileStorage)
    crawler_job_store = providers.Singleton(InMemoryCrawlerJobStore)
    job_executor = providers.Singleton(BackgroundJobExecutor, max_workers=2)

    staging_session_store = providers.Singleton(StagingSessionStore)
    staging_repository = providers.Singleton(
        StagingRepository,
        session_store=staging_session_store,
    )
    staging_query_helper = providers.Singleton(StagingQueryHelper)
    staging_query_service = providers.Singleton(
        StagingQueryService,
        helper=staging_query_helper,
    )

    staging_retraction_updater = providers.Singleton(
        StagingRetractionUpdater,
        repository=staging_repository,
        query_helper=staging_query_helper,
        logger=logger,
    )

    staging_row_manager = providers.Singleton(StagingRowManager, logger=logger)

    staging_service = providers.Singleton(
        StagingService,
        logger=logger,
        repository=staging_repository,
        query_service=staging_query_service,
        query_helper=staging_query_helper,
        retraction_updater=staging_retraction_updater,
        row_manager=staging_row_manager,
    )
    staging_query_parser = providers.Singleton(StagingQueryParser)
    manual_metadata_repository = providers.Singleton(ManualMetadataRepository)
    manual_metadata_merger = providers.Singleton(ManualMetadataMerger)
    manual_metadata_lookup = providers.Factory(
        ManualMetadataLookup,
        seed_selection_service=seed_selection_service,
    )
    manual_metadata_enricher = providers.Factory(
        ManualMetadataEnricher,
        seed_selection_service=seed_selection_service,
        repository=manual_metadata_repository,
        lookup_helper=manual_metadata_lookup,
        merger=manual_metadata_merger,
    )
    metadata_matcher_factory = providers.Singleton(
        APIMetadataMatcherFactory,
        logger=logger,
    )

    staging_match_service = providers.Factory(
        StagingMatchService,
        seed_selection_service=seed_selection_service,
        matcher_factory=metadata_matcher_factory,
        logger=logger,
    )

    retraction_doi_normalizer = providers.Singleton(RetractionDOINormalizer)
    retraction_metadata_builder = providers.Singleton(
        RetractionMetadataBuilder,
        normalizer=retraction_doi_normalizer,
    )
    retraction_cache_repository = providers.Singleton(
        RetractionCacheRepository,
        cache_dir=settings.RETRACTION_CACHE_DIR,
        logger=logger,
        normalizer=retraction_doi_normalizer,
    )

    retraction_service = providers.Singleton(
        RetractionWatchService,
        logger=logger,
        staging_service=staging_service,
        cache_repository=retraction_cache_repository,
        doi_normalizer=retraction_doi_normalizer,
        metadata_builder=retraction_metadata_builder,
        retraction_updater=staging_retraction_updater,
    )

    staged_file_storage = providers.Singleton(
        PersistentFileStorage,
        base_dir=settings.STAGED_FILES_DIR,
        logger=logger,
    )

    source_file_repository = providers.Singleton(
        SourceFileRepository,
        storage=staged_file_storage,
        logger=logger,
    )
    source_file_validator = providers.Singleton(SourceFileValidator)

    source_file_service = providers.Singleton(
        SourceFileService,
        logger=logger,
        repository=source_file_repository,
        validator=source_file_validator,
    )

    grobid_manager = providers.Singleton(GrobidManagerAdapter, logger=logger)
    pdf_metadata_extractor = providers.Singleton(MetadataExtractionAdapter, logger=logger)
    pdf_metadata_matcher = providers.Singleton(PDFMetadataMatcherAdapter, logger=logger)
    pdf_match_result_builder = providers.Singleton(PDFMatchResultBuilder, logger=logger)

    pdf_seed_service = providers.Singleton(
        PDFSeedService,
        logger=logger,
        upload_store=pdf_upload_store,
        file_storage=file_storage,
        source_file_service=source_file_service,
        grobid_manager=grobid_manager,
        metadata_extractor=pdf_metadata_extractor,
        metadata_matcher=pdf_metadata_matcher,
        match_result_builder=pdf_match_result_builder,
        api_factory=article_api_factory,
    )

    pdf_staging_row_builder = providers.Singleton(PDFStagingRowBuilder)
    pdf_matched_seed_builder = providers.Singleton(PDFMatchedSeedBuilder)
    pdf_seed_enricher = providers.Singleton(
        PDFSeedEnricher,
        logger=logger,
        api_factory=article_api_factory,
    )

    pdf_seed_workflow_service = providers.Factory(
        PDFSeedWorkflowService,
        pdf_seed_service=pdf_seed_service,
        staging_service=staging_service,
        seed_session_service=seed_session_service,
        logger=logger,
        row_builder=pdf_staging_row_builder,
        matched_seed_builder=pdf_matched_seed_builder,
        seed_enricher=pdf_seed_enricher,
    )
    
    zotero_client_adapter = providers.Singleton(ZoteroClientAdapter, logger=logger)
    zotero_metadata_extractor = providers.Singleton(ZoteroMetadataExtractorAdapter)
    zotero_matcher_adapter = providers.Singleton(ZoteroMatcherAdapter, logger=logger)
    zotero_session_store = providers.Singleton(ZoteroSessionStore)
    zotero_match_result_builder = providers.Singleton(ZoteroMatchResultBuilder, logger=logger)
    zotero_seed_enricher = providers.Singleton(
        ZoteroSeedEnricher,
        api_factory=article_api_factory,
        logger=logger,
    )

    zotero_seed_service = providers.Singleton(
        ZoteroSeedService,
        logger=logger,
        client_adapter=zotero_client_adapter,
        metadata_extractor=zotero_metadata_extractor,
        matcher_adapter=zotero_matcher_adapter,
        session_store=zotero_session_store,
        match_result_builder=zotero_match_result_builder,
        seed_enricher=zotero_seed_enricher,
        api_factory=article_api_factory,
    )
    
    keyword_repository = providers.Singleton(KeywordRepository)
    keyword_filter_builder = providers.Singleton(KeywordFilterBuilder)
    keyword_service = providers.Singleton(
        KeywordService,
        logger=logger,
        repository=keyword_repository,
        filter_builder=keyword_filter_builder,
    )

    configuration_service = providers.Singleton(ConfigurationService, logger=logger)

    integration_settings_repository = providers.Singleton(
        IntegrationSettingsRepository,
        logger=logger,
    )
    integration_settings_validator = providers.Singleton(IntegrationSettingsValidator)

    integration_settings_service = providers.Singleton(
        IntegrationSettingsService,
        logger=logger,
        repository=integration_settings_repository,
        validator=integration_settings_validator,
    )

    crawler_config_builder = providers.Singleton(
        CrawlerConfigBuilder,
        articlecrawler_path=settings.ARTICLECRAWLER_PATH,
        logger=logger,
    )

    crawler_job_runner = providers.Singleton(
        CrawlerJobRunner,
        logger=logger,
    )

    crawler_result_assembler = providers.Singleton(
        CrawlerResultAssembler,
        logger=logger,
    )

    crawler_execution_service = providers.Singleton(
        CrawlerExecutionService,
        logger=logger,
        articlecrawler_path=settings.ARTICLECRAWLER_PATH,
        job_store=crawler_job_store,
        job_executor=job_executor,
        config_builder=crawler_config_builder,
        job_runner=crawler_job_runner,
        result_assembler=crawler_result_assembler,
    )

    library_details_store = providers.Singleton(LibraryDetailsStore)
    library_path_resolver = providers.Singleton(
        LibraryPathResolver,
        articlecrawler_path=settings.ARTICLECRAWLER_PATH,
    )
    library_metadata_formatter = providers.Singleton(LibraryMetadataFormatter)
    library_workflow_runner = providers.Singleton(
        LibraryWorkflowRunner,
        logger=logger,
        metadata_formatter=library_metadata_formatter,
    )

    library_service = providers.Singleton(
        LibraryService,
        logger=logger,
        details_store=library_details_store,
        path_resolver=library_path_resolver,
        workflow_runner=library_workflow_runner,
    )

    library_edit_service = providers.Singleton(
        LibraryEditService,
        logger=logger,
        metadata_formatter=library_metadata_formatter,
        path_resolver=library_path_resolver,
    )

    topic_label_builder = providers.Singleton(TopicLabelBuilder)
    topic_result_formatter = providers.Singleton(
        TopicResultFormatter,
        label_builder=topic_label_builder,
    )
    topic_config_builder = providers.Singleton(TopicModelingConfigBuilder, logger=logger)
    topic_result_repository = providers.Singleton(TopicResultRepository)

    topic_modeling_service = providers.Singleton(
        TopicModelingService,
        logger=logger,
        config_builder=topic_config_builder,
        result_repository=topic_result_repository,
        result_formatter=topic_result_formatter,
    )

    author_topic_evolution_service = providers.Singleton(
        AuthorTopicEvolutionService,
        logger=logger
    )

    paper_metadata_service = providers.Singleton(
        PaperMetadataService,
        logger=logger
    )

    paper_catalog_repository = providers.Singleton(
        PaperCatalogRepository,
        articlecrawler_path=settings.ARTICLECRAWLER_PATH,
        logger=logger,
    )

    paper_annotation_repository = providers.Singleton(
        PaperAnnotationRepository,
        articlecrawler_path=settings.ARTICLECRAWLER_PATH,
        logger=logger,
    )

    catalog_query_builder = providers.Singleton(
        CatalogLazyFrameBuilder,
        catalog_repository=paper_catalog_repository,
        annotation_repository=paper_annotation_repository,
        mark_column=PaperCatalogService.MARK_COLUMN,
        allowed_marks=list(PaperCatalogService.ALLOWED_MARKS),
        identifier_fields=list(PaperCatalogService.IDENTIFIER_FIELDS),
    )

    catalog_column_options_builder = providers.Singleton(
        ColumnOptionsBuilder,
        columns=list(PaperCatalogService.COLUMN_OPTION_COLUMNS),
        max_filter_options=PaperCatalogService.MAX_FILTER_OPTIONS,
    )

    paper_catalog_exporter = providers.Singleton(
        PaperCatalogExporter,
        catalog_repository=paper_catalog_repository,
        annotation_repository=paper_annotation_repository,
        mark_column=PaperCatalogService.MARK_COLUMN,
    )

    paper_catalog_service = providers.Singleton(
        PaperCatalogService,
        catalog_repository=paper_catalog_repository,
        annotation_repository=paper_annotation_repository,
        logger=logger,
        query_builder=catalog_query_builder,
        column_options_builder=catalog_column_options_builder,
        catalog_exporter=paper_catalog_exporter,
    )

    library_route_helper = providers.Factory(
        LibraryRouteHelper,
        library_service=library_service,
        library_edit_service=library_edit_service,
        seed_selection_service=seed_selection_service,
        seed_session_service=seed_session_service,
    )

    staging_route_helper = providers.Factory(
        StagingRouteHelper,
        staging_service=staging_service,
        query_parser=staging_query_parser,
        manual_metadata_enricher=manual_metadata_enricher,
        match_service=staging_match_service,
        seed_session_service=seed_session_service,
    )

    seed_route_helper = providers.Factory(
        SeedRouteHelper,
        seed_selection_service=seed_selection_service,
    )
