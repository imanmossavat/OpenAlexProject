
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

# Optional ML features (need torch + sentence-transformers, see the `ml` extra).
# They are resolved lazily so `import ArticleCrawler` does not pull in the ML stack.
_LAZY_ML_EXPORTS = {
    'TitleSimilarityEngine': '.usecases.title_similarity_usecase',
    'PaperRecommender': '.usecases.recommender',
    'RecommenderEmbeddingModel': '.usecases.recommender',
}


def __getattr__(name):
    module_path = _LAZY_ML_EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib
    value = getattr(importlib.import_module(module_path, __name__), name)
    globals()[name] = value
    return value

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
    'AuthorInvestigation'
]