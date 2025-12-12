import logging
from typing import Any, Callable, Dict, Optional

from app.services.topics.helpers import (
    TopicModelingConfigBuilder,
    TopicResultRepository,
    TopicResultFormatter,
)


class TopicModelingService:
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        config_builder: Optional[TopicModelingConfigBuilder] = None,
        result_repository: Optional[TopicResultRepository] = None,
        result_formatter: Optional[TopicResultFormatter] = None,
        orchestrator_factory: Optional[Callable[[], Any]] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self._config_builder = config_builder or TopicModelingConfigBuilder(logger=self.logger)
        self._result_repository = result_repository or TopicResultRepository()
        self._result_formatter = result_formatter or TopicResultFormatter()
        self._orchestrator_factory = orchestrator_factory or self._default_orchestrator

    def run(self, library_details: Dict, model_type: str, num_topics: int) -> Dict[str, Any]:
        config = self._config_builder.build(library_details, model_type, num_topics)
        orchestrator = self._orchestrator_factory()
        clusters, overview_path = orchestrator.run_topic_modeling(
            library_path=config.library_path,
            model_type=config.model_type,
            num_topics=config.num_topics,
        )
        topics_folder = self._result_repository.ensure_topics_folder(config.library_path)
        normalized_overview = self._result_repository.normalize_overview_path(overview_path)
        formatted_clusters = self._result_formatter.format(clusters)
        return {
            "clusters": clusters,
            "formatted_clusters": formatted_clusters,
            "overview_path": normalized_overview,
            "topics_folder": topics_folder,
        }

    def _default_orchestrator(self):
        from ArticleCrawler.usecases.topic_modeling_usecase import TopicModelingOrchestrator

        return TopicModelingOrchestrator(logger=self.logger)

