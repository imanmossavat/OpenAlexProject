
import logging
from typing import Optional, List, Dict
from pathlib import Path


class AuthorTopicEvolutionService:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def _api(self, provider: str):
        from ArticleCrawler.api import create_api_provider
        return create_api_provider(provider, logger=self.logger)

    def search_authors(self, query: str, limit: int = 10, api_provider: str = "openalex") -> List[Dict]:
        api = self._api(api_provider)
        from ArticleCrawler.library.author_search_service import AuthorSearchService
        svc = AuthorSearchService(api, self.logger)
        authors = svc.search_authors(query, limit=limit)
        out: List[Dict] = []
        for a in authors:
            out.append({
                'id': a.id,
                'name': a.name,
                'works_count': getattr(a, 'works_count', 0) or 0,
                'cited_by_count': getattr(a, 'cited_by_count', 0) or 0,
                'institutions': getattr(a, 'institutions', []) or [],
                'orcid': getattr(a, 'orcid', None),
            })
        return out

    def run(self,
            author_id: str,
            model_type: str,
            num_topics: int,
            time_period_years: int,
            api_provider: str = "openalex",
            max_papers: Optional[int] = None,
            save_library: bool = False,
            library_path: Optional[str] = None,
            output_path: Optional[str] = None):
        # Build dependencies
        api = self._api(api_provider)
        from ArticleCrawler.library.author_search_service import AuthorSearchService
        from ArticleCrawler.library.library_manager import LibraryManager
        from ArticleCrawler.usecases.topic_modeling_usecase import TopicModelingOrchestrator
        from ArticleCrawler.library.temporal_analysis_service import TemporalAnalysisService
        from ArticleCrawler.visualization.topic_evolution_visualizer import LineChartVisualizer
        from ArticleCrawler.utils.library_temp_manager import TempLibraryManager
        from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
        from ArticleCrawler.config.text_config import TextProcessingConfig
        from ArticleCrawler.config.temporal_config import TemporalAnalysisConfig
        from ArticleCrawler.visualization.visualization_config import VisualizationConfig

        author_search = AuthorSearchService(api, self.logger)
        candidates = author_search.search_authors(author_id, limit=1)
        if not candidates:
            raise ValueError(f"Author not found: {author_id}")
        author = candidates[0]

        text_cfg = TextProcessingConfig(num_topics=num_topics)
        topic_orch = TopicModelingOrchestrator(topic_config=text_cfg, logger=self.logger)
        temp_mgr = TempLibraryManager(self.logger)
        lib_mgr = LibraryManager(self.logger)
        temporal_cfg = TemporalAnalysisConfig(time_period_years=time_period_years)
        temporal_analyzer = TemporalAnalysisService(temporal_cfg, self.logger)
        viz_cfg = VisualizationConfig()
        visualizer = LineChartVisualizer(viz_cfg, self.logger)
        md_writer = MarkdownFileGenerator(storage_and_logging_options=None, api_provider_type=api_provider)

        from ArticleCrawler.usecases.author_topic_evolution_usecase import AuthorTopicEvolutionUseCase
        use_case = AuthorTopicEvolutionUseCase(
            api_provider=api,
            author_search_service=author_search,
            library_manager=lib_mgr,
            topic_orchestrator=topic_orch,
            temporal_analyzer=temporal_analyzer,
            visualizer=visualizer,
            temp_library_manager=temp_mgr,
            markdown_writer=md_writer,
            logger=self.logger,
        )

        lib_path = Path(library_path) if library_path else None
        out_path = Path(output_path) if output_path else None
        result = use_case.run(
            author=author,
            model_type=model_type,
            num_topics=num_topics,
            save_library=bool(save_library and lib_path),
            library_path=lib_path,
            output_path=out_path,
            max_papers=max_papers,
        )

        return result

