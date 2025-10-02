# Import from new structure
from .api import create_api_provider, BaseAPIProvider
from .data import DataManager, DataCoordinator, FrameManager
from .config import (
    APIConfig, SamplingConfig, TextProcessingConfig,
    StorageAndLoggingConfig, GraphConfig, RetractionConfig, StoppingConfig,
    # Backward compatibility
    SamplingOptions, TextOptions, StorageAndLoggingOptions,
    GraphOptions, RetractionOptions, StoppingOptions
)
from .text_processing import TextAnalysisManager
from .sampling import Sampler
from .crawler import Crawler
from .graph import GraphManager, GraphProcessing  # ← CHANGED

# Import from legacy locations
from .LogManager.crawler_logger import CrawlerLogger
from .DataManagement.data_storage import DataStorage
from .papervalidation.retraction_watch_manager import RetractionWatchManager
from .usecases.author_investigation import AuthorInvestigation
from .usecases.title_similarity_usecase import TitleSimilarityEngine
from .usecases.recommender import PaperRecommender, RecommenderEmbeddingModel

__all__ = [
    # New architecture
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
    # Backward compatibility
    'SamplingOptions',
    'TextOptions',
    'StorageAndLoggingOptions',
    'GraphOptions',
    'RetractionOptions',
    'StoppingOptions',
    # Legacy components
    'CrawlerLogger',
    'DataStorage',
    'RetractionWatchManager',
    'AuthorInvestigation',
    'TitleSimilarityEngine',
    'PaperRecommender',
    'RecommenderEmbeddingModel'
]