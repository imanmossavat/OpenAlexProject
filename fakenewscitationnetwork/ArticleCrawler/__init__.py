
from .api import create_api_provider, BaseAPIProvider
from .data import DataManager, DataCoordinator, FrameManager
from .config import (
    APIConfig, SamplingConfig, TextProcessingConfig,
    StorageAndLoggingConfig, GraphConfig, RetractionConfig, StoppingConfig,
    SamplingOptions, TextOptions, StorageAndLoggingOptions,
    GraphOptions, RetractionOptions, StoppingOptions
)
from .text_processing import TextAnalysisManager
from .sampling import Sampler
from .crawler import Crawler
from .graph import GraphManager, GraphProcessing
from .pdf_processing import (
    PDFProcessor,
    PDFMetadataExtractor,
    APIMetadataMatcher,
    DockerManager,
    PDFMetadata,
    PDFProcessingResult,
    APIMatchResult
)
from .LogManager.crawler_logger import CrawlerLogger
from .DataManagement.data_storage import DataStorage
from .papervalidation.retraction_watch_manager import RetractionWatchManager
from .usecases.author_investigation import AuthorInvestigation
from .usecases.title_similarity_usecase import TitleSimilarityEngine
from .usecases.recommender import PaperRecommender, RecommenderEmbeddingModel

__all__ = [
    'create_api_provider',
    'BaseAPIProvider',
    'DataManager',
    'DataCoordinator',
    'FrameManager',
    'APIConfig',
    'SamplingConfig',
    'TextProcessingConfig',
    'StorageAndLoggingConfig',
    'GraphConfig',
    'RetractionConfig',
    'StoppingConfig',
    'TextAnalysisManager',
    'Sampler',
    'Crawler',
    'GraphManager',
    'GraphProcessing',
    'PDFProcessor',
    'PDFMetadataExtractor',
    'APIMetadataMatcher',
    'DockerManager',
    'PDFMetadata',
    'PDFProcessingResult',
    'APIMatchResult',
    'SamplingOptions',
    'TextOptions',
    'StorageAndLoggingOptions',
    'GraphOptions',
    'RetractionOptions',
    'StoppingOptions',
    'CrawlerLogger',
    'DataStorage',
    'RetractionWatchManager',
    'AuthorInvestigation',
    'TitleSimilarityEngine',
    'PaperRecommender',
    'RecommenderEmbeddingModel'
]