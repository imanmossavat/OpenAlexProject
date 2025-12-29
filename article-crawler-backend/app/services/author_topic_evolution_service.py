
import logging
from typing import Optional, List, Dict
from pathlib import Path
import tempfile


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
            output_path: Optional[str] = None,
            author_name: Optional[str] = None):
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
        search_query = author_name or author_id
        candidates = author_search.search_authors(search_query, limit=10)

        normalized_target = self._normalize_author_id(author_id)
        author = None
        for candidate in candidates:
            if self._normalize_author_id(candidate.id) == normalized_target:
                author = candidate
                break
        if not author and candidates:
            author = candidates[0]

        if not author:
            raise ValueError(f"Author not found: {author_id}")

        text_cfg = TextProcessingConfig(num_topics=num_topics)
        topic_orch = TopicModelingOrchestrator(topic_config=text_cfg, logger=self.logger)
        temp_mgr = TempLibraryManager(self.logger)
        lib_mgr = LibraryManager(self.logger)
        temporal_cfg = TemporalAnalysisConfig(time_period_years=time_period_years)
        temporal_analyzer = TemporalAnalysisService(temporal_cfg, self.logger)
        viz_cfg = VisualizationConfig()
        visualizer = LineChartVisualizer(viz_cfg, self.logger)
        md_writer = MarkdownFileGenerator(
            storage_and_logging_options=self._create_storage_config(),
            api_provider_type=api_provider
        )

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

    def _normalize_author_id(self, author_id: str) -> str:
        if not author_id:
            return ""
        author_id = author_id.strip()
        if author_id.startswith("https://openalex.org/"):
            author_id = author_id.split('/')[-1]
        return author_id.upper()

    def _create_storage_config(self):
        class BackendStorageConfig:
            def __init__(self, base_path: Path):
                self.experiment_file_name = "author_topic_evolution"
                self.vault_folder = base_path
                self.abstracts_folder = base_path / "papers"
                self.figure_folder = base_path / "figures"
                self.metadata_folder = base_path / "metadata"
                self.summary_folder = base_path / "summary"
                self.open_vault_folder = False
                self.summary_structured_folder = self.summary_folder / "structured"
                self.manifest_folder = base_path / "manifest"

        temp_dir = Path(tempfile.mkdtemp(prefix="author_topic_evolution_"))
        return BackendStorageConfig(temp_dir)

