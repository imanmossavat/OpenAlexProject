

import logging
from typing import Optional, Dict
from pathlib import Path


class TopicModelingService:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def run(self, library_details: Dict, model_type: str, num_topics: int):
        from ArticleCrawler.usecases.topic_modeling_usecase import TopicModelingOrchestrator
        lib_path = Path(library_details.get('path'))
        orch = TopicModelingOrchestrator(logger=self.logger)
        clusters, overview_path = orch.run_topic_modeling(
            library_path=lib_path,
            model_type=model_type,
            num_topics=num_topics,
        )
        topics_folder = lib_path / 'topics'
        return clusters, overview_path, topics_folder

