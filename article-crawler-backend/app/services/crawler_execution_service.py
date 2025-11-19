
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import pandas as pd

from ArticleCrawler.crawler import Crawler
from ArticleCrawler.config.crawler_initialization import CrawlerParameters

from app.core.stores.crawler_job_store import (
    CrawlerJobStore,
    InMemoryCrawlerJobStore,
)
from app.core.executors.background import BackgroundJobExecutor


class CrawlerExecutionService:

    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        articlecrawler_path: Optional[str] = None,
        job_store: Optional[CrawlerJobStore] = None,
        job_executor: Optional[BackgroundJobExecutor] = None,
    ):
        """Initialize the crawler execution service."""
        self.logger = logger or logging.getLogger(__name__)
        
        self._job_store = job_store or InMemoryCrawlerJobStore()
        self._executor = job_executor or BackgroundJobExecutor()
        
        self.articlecrawler_path: Optional[Path] = Path(articlecrawler_path) if articlecrawler_path else None
        
        if self.articlecrawler_path:
            self.logger.info(f"ArticleCrawler path configured: {self.articlecrawler_path}")
    
    def start_crawler(
        self,
        session_id: str,
        session_data: Dict
    ) -> str:
        """
        Start a crawler job with configuration from session.
        
        Args:
            session_id: Session identifier
            session_data: Complete session data with config and seeds
            
        Returns:
            job_id: Unique job identifier
        """
        if not self.articlecrawler_path:
            raise ValueError("ArticleCrawler path not configured")
        
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        self.logger.info(f"Starting crawler job {job_id} for session {session_id}")
        
        job_data = {
            "job_id": job_id,
            "session_id": session_id,
            "status": "running",
            "current_iteration": 0,
            "max_iterations": session_data.get("configuration", {}).get("max_iterations", 1),
            "papers_collected": 0,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None
        }
        self._job_store.create_job(job_id, job_data)
        
        self._executor.submit(self._run_crawler, job_id, session_data)
        
        return job_id
    
    def _run_crawler(
        self,
        job_id: str,
        session_data: Dict
    ):
        """
        Execute the crawler in background thread.
        
        Args:
            job_id: Job identifier
            session_data: Session configuration
        """
        try:
            job_logger = logging.LoggerAdapter(self.logger, {"job_id": job_id})
            job_logger.info("Job %s: Building crawler configuration", job_id)
            
            from ArticleCrawler.cli.models.experiment_config import ExperimentConfig
            
            config_dict = session_data.get("configuration", {})
            keywords = session_data.get("keywords", [])

            seeds: List[str]
            library_path_str = session_data.get("library_path")
            library_name = session_data.get("library_name")
            if library_path_str:
                from ArticleCrawler.library.library_manager import LibraryManager
                from ArticleCrawler.library.paper_file_reader import PaperFileReader
                lib_logger = self.logger
                lm = LibraryManager(lib_logger)
                papers_dir = lm.get_papers_directory(Path(library_path_str))
                reader = PaperFileReader(lib_logger)
                paper_datas = reader.read_papers_from_directory(papers_dir)
                seeds = [pd_obj.paper_id for pd_obj in paper_datas if getattr(pd_obj, 'paper_id', None)]
                if not seeds:
                    raise ValueError(f"No papers found in library at {library_path_str}")
                try:
                    lib_config = lm.load_library_config(Path(library_path_str))
                    if lib_config and not config_dict.get("api_provider"):
                        config_dict["api_provider"] = getattr(lib_config, "api_provider", None) or config_dict.get("api_provider")
                except Exception:
                    pass
            else:
                seeds = [seed["paper_id"] for seed in session_data.get("seeds", [])]
            
            experiment_config = ExperimentConfig(
                name=f"crawler_{job_id}",
                seeds=seeds,
                keywords=keywords,
                max_iterations=config_dict.get("max_iterations", 1),
                papers_per_iteration=config_dict.get("papers_per_iteration", 1),
                api_provider=config_dict.get("api_provider", "openalex"),
                api_retries=config_dict.get("api_retries", 3),
                no_keyword_lambda=config_dict.get("no_keyword_lambda", 0.2),
                sampling_hyperparams=config_dict.get("sampling_hyperparams", {"year": 0.3, "centrality": 1.0}),
                ignored_venues=config_dict.get("ignored_venues", ["", "ArXiv", "medRxiv", "WWW"]),
                min_abstract_length=config_dict.get("min_abstract_length", 120),
                num_topics=config_dict.get("num_topics", 20),
                topic_model=config_dict.get("topic_model", "NMF"),
                stemmer=config_dict.get("stemmer", "Porter"),
                language=config_dict.get("language", "en"),
                save_figures=config_dict.get("save_figures", True),
                random_state=config_dict.get("random_state", 42),
                include_author_nodes=config_dict.get("include_author_nodes", False),
                max_centrality_iterations=config_dict.get("max_centrality_iterations", 1000),
                enable_retraction_watch=config_dict.get("enable_retraction_watch", True),
                avoid_retraction_in_sampler=config_dict.get("avoid_retraction_in_sampler", False),
                avoid_retraction_in_reporting=config_dict.get("avoid_retraction_in_reporting", True),
                root_folder=self.articlecrawler_path / "experiments" / f"job_{job_id}",
                log_level=config_dict.get("log_level", "INFO"),
                open_vault_folder=False,
                library_path=Path(library_path_str) if library_path_str else None,
                library_name=library_name
            )
            
            crawler_configs = experiment_config.to_crawler_configs()
            
            api_config = crawler_configs["api_config"]
            sampling_config = crawler_configs["sampling_config"]
            text_config = crawler_configs["text_config"]
            storage_config = crawler_configs["storage_config"]
            graph_config = crawler_configs["graph_config"]
            retraction_config = crawler_configs["retraction_config"]
            stopping_config = crawler_configs["stopping_config"]
            
            storage_config.root_folder.mkdir(parents=True, exist_ok=True)
            
            crawl_params = CrawlerParameters(
                seed_paperid=seeds,
                keywords=keywords
            )
            
            from ArticleCrawler.DataManagement.markdown_writer import MarkdownFileGenerator
            md_gen = MarkdownFileGenerator(
                storage_and_logging_options=storage_config,
                api_provider_type=api_config.provider_type
            )
            
            self.logger.info(f"Job {job_id}: Initializing crawler")
            
            crawler = Crawler(
                crawl_initial_condition=crawl_params,
                stopping_criteria_config=stopping_config,
                api_config=api_config,
                sampling_config=sampling_config,
                text_config=text_config,
                storage_config=storage_config,
                graph_config=graph_config,
                retraction_config=retraction_config,
                md_generator=md_gen
            )
            
            job_logger.info("Job %s: Starting crawl process", job_id)
            
            crawler.crawl()
            

            current_job = self._job_store.get_job(job_id) or {}
            max_iterations = current_job.get("max_iterations") or session_data.get("configuration", {}).get("max_iterations", 1)
            self._job_store.update_job(
                job_id,
                current_iteration=max_iterations,
                papers_collected=len(crawler.data_coordinator.frames.df_paper_metadata),
            )
            
            job_logger.info("Job %s: Crawling completed, generating markdown files", job_id)
            
            crawler.generate_markdown_files()
            
            job_logger.info("Job %s: Running analysis and reporting", job_id)
            
            crawler.analyze_and_report(
                save_figures=text_config.save_figures,
                num_topics=text_config.num_topics
            )
            
            self._job_store.store_crawler(job_id, crawler)
            
            self._job_store.update_job(
                job_id,
                status="completed",
                completed_at=datetime.utcnow(),
            )
            
            job_logger.info("Job %s: Completed successfully", job_id)
            
        except Exception as e:
            logging.LoggerAdapter(self.logger, {"job_id": job_id}).error(
                "Job %s: Failed with error: %s", job_id, e, exc_info=True
            )
            self._job_store.update_job(
                job_id,
                status="failed",
                error_message=str(e),
                completed_at=datetime.utcnow(),
            )
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        return self._job_store.get_job(job_id)
    
    def get_results(self, job_id: str) -> Optional[Dict]:
        job = self._job_store.get_job(job_id)
        if not job or job.get("status") != "completed":
            return None

        crawler = self._job_store.get_crawler(job_id)
        if not crawler:
            return None
        
        return self._extract_results(job_id, crawler)
    
    def _extract_results(self, job_id: str, crawler: Crawler) -> Dict:

        analysis = crawler.text_processor.analysis
        df_results = analysis.get("df_merge_meta_centralities_topics")

        temporal_distribution: List[Dict] = []
        if df_results is not None and not df_results.empty and "year" in df_results.columns:
            try:
                year_series = pd.to_numeric(df_results["year"], errors="coerce").dropna().astype(int)
                year_counts = year_series.value_counts(sort=False).sort_index()
                temporal_distribution = [
                    {"year": int(year), "paper_count": int(count)}
                    for year, count in year_counts.items()
                ]
            except Exception:
                temporal_distribution = []

        top_papers = self._get_top_papers(df_results, crawler)
        topics = self._get_topics_overview(df_results, crawler)
        top_authors = self._get_top_authors(df_results, crawler.data_coordinator)

        DG = crawler.graph_manager.DG if hasattr(crawler, 'graph_manager') else None
        total_nodes = len(DG.nodes()) if DG is not None else 0
        total_edges = len(DG.edges()) if DG is not None else 0
        paper_nodes = 0
        author_nodes = 0
        if DG is not None:
            try:
                paper_nodes = sum(1 for _, d in DG.nodes(data=True) if d.get('ntype') == 'paper')
                author_nodes = sum(1 for _, d in DG.nodes(data=True) if d.get('ntype') == 'author')
            except Exception:
                pass

        total_iterations = (self._job_store.get_job(job_id) or {}).get("current_iteration", 0)
        retracted_papers = 0
        if df_results is not None:
            retracted_col = None
            for c in ["retracted", "isRetracted", "is_retracted"]:
                if c in df_results.columns:
                    retracted_col = c
                    break
            if retracted_col is not None:
                s = df_results[retracted_col]
                try:
                    if s.dtype == bool:
                        retracted_papers = int(s.sum())
                    elif pd.api.types.is_numeric_dtype(s):
                        retracted_papers = int(pd.to_numeric(s, errors="coerce").fillna(0).astype(int).sum())
                    else:
                        s_str = s.astype(str).str.strip().str.lower()
                        s_bool = s_str.isin(["true", "1", "yes", "y", "retracted"])
                        retracted_papers = int(s_bool.sum())
                except Exception:
                    retracted_papers = 0

        results = {
            "job_id": job_id,
            "network_overview": {
                "total_nodes": int(total_nodes),
                "total_edges": int(total_edges),
                "paper_nodes": int(paper_nodes if paper_nodes else (len(df_results) if df_results is not None else 0)),
                "author_nodes": int(author_nodes),
                "total_papers": int(len(df_results) if df_results is not None else 0),
                "total_iterations": int(total_iterations),
                "total_topics": int(len(topics)),
                "retracted_papers": int(retracted_papers)
            },
            "temporal_distribution": temporal_distribution,
            "top_papers": top_papers,
            "topics": topics,
            "top_authors": top_authors
        }

        return results
    
    def _select_centrality_column(self, df: pd.DataFrame) -> Optional[str]:
        """Select the best available centrality-like column from a DataFrame."""
        candidates = [
            "centrality_in",
            "in_centrality",
            "centrality",
            "in_degree_centrality",
            "centrality_in_degree",
            "centrality (in)",
            "centrality (out)",
            "eigen_centrality",
            "pagerank"
        ]
        for col in candidates:
            if col in df.columns:
                return col
        return None

    def _select_citation_count_column(self, df: pd.DataFrame) -> Optional[str]:
        """Select a citation count-like column if available."""
        candidates = [
            "citation_count",
            "citationCount",
            "citedByCount",
            "cited_by_count",
            "numCitations",
            "citations_count"
        ]
        for col in candidates:
            if col in df.columns:
                return col
        return None

    def _get_top_papers(
        self,
        df_results: pd.DataFrame,
        crawler: Crawler,
        limit: int = 50
    ) -> List[Dict]:
        """Extract top papers by centrality score."""
        from ArticleCrawler.utils.url_builder import PaperURLBuilder
        url_builder = PaperURLBuilder()

        score_col = self._select_centrality_column(df_results)
        if score_col and score_col in df_results.columns:
            df_sorted = df_results.sort_values(score_col, ascending=False).head(limit)
        else:
            cite_col = self._select_citation_count_column(df_results)
            if cite_col:
                df_sorted = df_results.sort_values(cite_col, ascending=False).head(limit)
            else:
                df_sorted = df_results.head(limit)
        
        papers = []
        for _, row in df_sorted.iterrows():

            authors_field = row.get('authors', [])
            if isinstance(authors_field, list):
                if len(authors_field) > 0 and isinstance(authors_field[0], dict):
                    authors_list = [
                        (a.get('name') or a.get('authorName') or '').strip()
                        for a in authors_field
                        if isinstance(a, dict)
                    ]
                else:
                    authors_list = [str(a) for a in authors_field]
            else:
                authors_list = []

            cite_col = self._select_citation_count_column(df_results)
            year_val = row.get('year')
            year_int = None
            if pd.notna(year_val):
                try:
                    year_int = int(year_val)
                except Exception:
                    try:
                        year_int = int(float(year_val))
                    except Exception:
                        year_int = None

            cite_val = row.get(cite_col) if cite_col else None
            cite_int = None
            if cite_val is not None and pd.notna(cite_val):
                try:
                    cite_int = int(cite_val)
                except Exception:
                    try:
                        cite_int = int(float(cite_val))
                    except Exception:
                        cite_int = None
            paper = {
                "paper_id": row['paperId'],
                "title": row.get('title', ''),
                "authors": authors_list,
                "year": year_int,
                "venue": row.get('venue', ''),
                "doi": row.get('doi', ''),
                "citation_count": cite_int,
                "centrality_score": float(row.get(score_col, 0.0)) if score_col else 0.0,
                "is_seed": bool(row.get('isSeed', False)),
                "is_retracted": bool(row.get('retracted', row.get('isRetracted', False))),
                "url": url_builder.build_url(row['paperId'], crawler.api_config.provider_type)
            }
            papers.append(paper)
        
        return papers
    
    def _get_topics_overview(
        self,
        df_results: pd.DataFrame,
        crawler: Crawler
    ) -> List[Dict]:
        """Extract topics overview."""
        topic_model_type = getattr(crawler.text_config, 'default_topic_model_type', 'NMF')
        topic_col = f"{topic_model_type.lower()}_topic"
        
        if topic_col not in df_results.columns:
            return []
        
        topic_results = crawler.text_processor.topicmodeling.results.get(
            topic_model_type.upper(), {}
        )
        top_words_list = topic_results.get('top_words', [])
        
        topics = []
        topic_counts = df_results[topic_col].value_counts().sort_index()
        
        for topic_id, count in topic_counts.items():
            if pd.isna(topic_id) or topic_id < 0:
                continue
            
            topic_id = int(topic_id)
            
            topic_papers = df_results[df_results[topic_col] == topic_id]['paperId'].tolist()
            
            top_words = []
            if topic_id < len(top_words_list):
                top_words = top_words_list[topic_id]
            
            topic_label = f"Topic {topic_id}"
            if top_words:
                topic_label = " ".join(top_words[:5])
            
            topics.append({
                "topic_id": topic_id,
                "topic_label": topic_label,
                "paper_count": int(count),
                "top_words": top_words,
                "paper_ids": topic_papers
            })
        
        return topics
    
    def _get_top_authors(
        self,
        df_results: pd.DataFrame,
        data_coord,
        limit: int = 50
    ) -> List[Dict]:
        """Extract top authors by centrality."""
        df_author = data_coord.frames.df_author
        df_paper_author = data_coord.frames.df_paper_author
        
        if df_author.empty:
            return []
        
        author_metrics = []
        
        for _, author_row in df_author.iterrows():
            author_id = author_row['authorId']
            
            author_papers = df_paper_author[
                df_paper_author['authorId'] == author_id
            ]['paperId'].tolist()
            
            if not author_papers:
                continue
            
            author_paper_data = df_results[df_results['paperId'].isin(author_papers)]
            
            if author_paper_data.empty:
                continue
            
            score_col = self._select_centrality_column(author_paper_data)
            if score_col and score_col in author_paper_data.columns:
                centrality_series = pd.to_numeric(author_paper_data[score_col], errors="coerce").fillna(0.0)
                avg_centrality = float(centrality_series.mean())
            else:
                avg_centrality = 0.0
            cite_col = self._select_citation_count_column(author_paper_data)
            if cite_col and cite_col in author_paper_data.columns:
                total_citations_val = pd.to_numeric(author_paper_data[cite_col], errors="coerce").fillna(0).sum()
                total_citations = int(total_citations_val) if pd.notna(total_citations_val) else 0
            else:
                total_citations = 0
            
            author_metrics.append({
                "author_id": author_id,
                "author_name": author_row.get('authorName', ''),
                "paper_count": len(author_papers),
                "centrality_score": float(avg_centrality),
                "total_citations": int(total_citations) if pd.notna(total_citations) else 0
            })
        
        author_metrics.sort(key=lambda x: x['centrality_score'], reverse=True)
        
        return author_metrics[:limit]
    
    def get_topic_papers(
        self,
        job_id: str,
        topic_id: int
    ) -> Optional[Dict]:

        if job_id not in self.completed_crawlers:
            return None
        
        crawler = self.completed_crawlers[job_id]
        analysis = crawler.text_processor.analysis
        df_results = analysis.get("df_merge_meta_centralities_topics")
        
        topic_model_type = getattr(crawler.text_config, 'default_topic_model_type', 'NMF')
        topic_col = f"{topic_model_type.lower()}_topic"
        
        if topic_col not in df_results.columns:
            return None
        
        topic_papers_df = df_results[df_results[topic_col] == topic_id]
        
        if topic_papers_df.empty:
            return None
        
        topic_results = crawler.text_processor.topicmodeling.results.get(
            topic_model_type.upper(), {}
        )
        top_words_list = topic_results.get('top_words', [])
        
        topic_label = f"Topic {topic_id}"
        if topic_id < len(top_words_list):
            top_words = top_words_list[topic_id]
            topic_label = " ".join(top_words[:5])
        
        papers = self._get_top_papers(topic_papers_df, crawler, limit=len(topic_papers_df))
        
        return {
            "topic_id": topic_id,
            "topic_label": topic_label,
            "papers": papers,
            "total_count": len(papers)
        }
    
    def list_jobs(self) -> List[Dict]:
        """List all crawler jobs."""
        return self._job_store.list_jobs()
