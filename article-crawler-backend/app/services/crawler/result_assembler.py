from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from ArticleCrawler.api.api_factory import create_api_provider
from ArticleCrawler.api.base_api import BaseAPIProvider
from ArticleCrawler.crawler import Crawler
from ArticleCrawler.library.models import PaperData
from ArticleCrawler.utils.url_builder import PaperURLBuilder
from app.services.crawler.entity_papers_builder import RemoteEntityPapersBuilder


class CrawlerResultAssembler:
    """Create API-friendly payloads from ArticleCrawler instances."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self._api_clients: Dict[str, BaseAPIProvider] = {}
        self._entity_papers_builder = RemoteEntityPapersBuilder(
            self.logger,
            self._get_api_client,
        )

    def assemble(
        self,
        job_id: str,
        crawler: Crawler,
        job_metadata: Optional[Dict],
    ) -> Dict:
        analysis = crawler.text_processor.analysis
        df_results = analysis.get("df_merge_meta_centralities_topics")

        temporal_distribution: List[Dict] = []
        if df_results is not None and not df_results.empty and "year" in df_results.columns:
            try:
                year_series = (
                    pd.to_numeric(df_results["year"], errors="coerce").dropna().astype(int)
                )
                year_counts = year_series.value_counts(sort=False).sort_index()
                temporal_distribution = [
                    {"year": int(year), "paper_count": int(count)}
                    for year, count in year_counts.items()
                ]
            except Exception:
                temporal_distribution = []

        top_papers = self._get_top_papers(df_results, crawler)
        topics = self._get_topics_overview(df_results, crawler)

        summary_structured_folder = getattr(
            crawler.storage_config, "summary_structured_folder", None
        )
        structured_authors = self._load_structured_summary(
            summary_structured_folder, "top_authors"
        )
        if structured_authors:
            top_authors = self._format_authors_from_summary(structured_authors)
        else:
            top_authors = self._get_top_authors(df_results, crawler.data_coordinator)

        structured_venues = self._load_structured_summary(
            summary_structured_folder, "top_venues"
        )
        if structured_venues:
            top_venues = self._format_venues_from_summary(structured_venues)
        else:
            top_venues = self._compute_top_venues(crawler.data_coordinator)

        DG = crawler.graph_manager.DG if hasattr(crawler, "graph_manager") else None
        total_nodes = len(DG.nodes()) if DG is not None else 0
        total_edges = len(DG.edges()) if DG is not None else 0
        paper_nodes = 0
        author_nodes = 0
        if DG is not None:
            try:
                paper_nodes = sum(
                    1 for _, data in DG.nodes(data=True) if data.get("ntype") == "paper"
                )
                author_nodes = sum(
                    1 for _, data in DG.nodes(data=True) if data.get("ntype") == "author"
                )
            except Exception:
                pass

        total_iterations = (job_metadata or {}).get("current_iteration", 0)
        retracted_papers = 0
        if df_results is not None:
            retracted_col = None
            for column in ["retracted", "isRetracted", "is_retracted"]:
                if column in df_results.columns:
                    retracted_col = column
                    break
            if retracted_col is not None:
                series = df_results[retracted_col]
                try:
                    if series.dtype == bool:
                        retracted_papers = int(series.sum())
                    elif pd.api.types.is_numeric_dtype(series):
                        retracted_papers = int(
                            pd.to_numeric(series, errors="coerce")
                            .fillna(0)
                            .astype(int)
                            .sum()
                        )
                    else:
                        s_str = series.astype(str).str.strip().str.lower()
                        s_bool = s_str.isin(["true", "1", "yes", "y", "retracted"])
                        retracted_papers = int(s_bool.sum())
                except Exception:
                    retracted_papers = 0

        results = {
            "job_id": job_id,
            "network_overview": {
                "total_nodes": int(total_nodes),
                "total_edges": int(total_edges),
                "paper_nodes": int(
                    paper_nodes
                    if paper_nodes
                    else (len(df_results) if df_results is not None else 0)
                ),
                "author_nodes": int(author_nodes),
                "total_papers": int(len(df_results) if df_results is not None else 0),
                "total_iterations": int(total_iterations),
                "total_topics": int(len(topics)),
                "retracted_papers": int(retracted_papers),
            },
            "temporal_distribution": temporal_distribution,
            "top_papers": top_papers,
            "topics": topics,
            "top_authors": top_authors,
            "top_venues": top_venues,
        }

        return results

    def build_topic_papers(
        self,
        crawler: Crawler,
        topic_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Optional[Dict]:
        analysis = getattr(crawler.text_processor, "analysis", None) or {}
        df_results = analysis.get("df_merge_meta_centralities_topics")
        if df_results is None or df_results.empty:
            return None

        topic_model_type = getattr(
            crawler.text_config, "default_topic_model_type", "NMF"
        )
        topic_col = f"{topic_model_type.lower()}_topic"
        if topic_col not in df_results.columns:
            return None

        topic_series = pd.to_numeric(df_results[topic_col], errors="coerce")
        topic_frame = df_results[topic_series == topic_id]
        if topic_frame is None or topic_frame.empty:
            return None

        sorted_df = self._sort_topic_dataframe(topic_frame)
        total = len(sorted_df)
        normalized_page_size = max(1, min(int(page_size or 1), 50))
        total_pages = max(1, (total + normalized_page_size - 1) // normalized_page_size)
        current_page = min(max(1, int(page or 1)), total_pages)
        start = (current_page - 1) * normalized_page_size
        end = start + normalized_page_size
        paged_df = sorted_df.iloc[start:end]

        provider_type = getattr(getattr(crawler, "api_config", None), "provider_type", "openalex")
        url_builder = PaperURLBuilder()
        score_column = self._select_centrality_column(df_results)

        fallback_lookup: Dict[str, Dict] = {}
        paper_ids: List[str] = []
        for _, row in paged_df.iterrows():
            pid = row.get("paperId")
            if not pid:
                continue
            fallback_lookup[pid] = row.to_dict()
            paper_ids.append(pid)

        metadata_map: Dict[str, PaperData] = {}
        normalized_ids: Dict[str, Optional[str]] = {
            pid: self._clean_provider_id(pid) for pid in paper_ids
        }
        api_client = self._get_api_client(provider_type)
        if api_client and any(normalized_ids.values()):
            lookup_ids = [pid for pid in normalized_ids.values() if pid]
            metadata_map = self._fetch_provider_metadata(api_client, lookup_ids)

        papers: List[Dict] = []
        for pid in paper_ids:
            normalized_pid = normalized_ids.get(pid)
            paper_data = metadata_map.get(normalized_pid) if normalized_pid else None
            fallback = fallback_lookup.get(pid, {})
            entry = self._build_topic_paper_entry(
                pid,
                paper_data,
                fallback,
                provider_type,
                url_builder,
                score_column,
            )
            papers.append(entry)

        topic_results = crawler.text_processor.topicmodeling.results.get(
            topic_model_type.upper(), {}
        )
        top_words_list = topic_results.get("top_words", [])
        topic_label = f"Topic {topic_id}"
        if 0 <= topic_id < len(top_words_list):
            top_words = top_words_list[topic_id]
            if top_words:
                topic_label = " ".join(top_words[:5])

        return {
            "topic_id": int(topic_id),
            "topic_label": topic_label,
            "page": current_page,
            "page_size": normalized_page_size,
            "total": int(total),
            "papers": papers,
        }

    def build_author_papers(
        self,
        crawler: Crawler,
        author_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Optional[Dict]:
        return self._entity_papers_builder.build_author_papers(
            crawler,
            author_id,
            page=page,
            page_size=page_size,
            entry_builder=self._build_remote_paper_entry,
        )

    def build_venue_papers(
        self,
        crawler: Crawler,
        venue_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Optional[Dict]:
        return self._entity_papers_builder.build_venue_papers(
            crawler,
            venue_id,
            page=page,
            page_size=page_size,
            entry_builder=self._build_remote_paper_entry,
        )

    _CENTRALITY_COLUMN_MAP = {
        "centrality_in": [
            "centrality_in",
            "in_centrality",
            "centrality",
            "in_degree_centrality",
            "centrality_in_degree",
            "centrality (in)",
        ],
        "centrality_out": [
            "centrality_out",
            "out_centrality",
            "out_degree_centrality",
            "centrality (out)",
        ],
        "eigenvector_in": [
            "eigen_centrality",
            "eigenvector_centrality",
            "eigen_centrality_in",
        ],
        "eigenvector_out": [
            "eigen_centrality_out",
            "eigenvector_centrality_out",
        ],
        "pagerank": ["pagerank"],
    }

    def _select_centrality_column(self, df: pd.DataFrame) -> Optional[str]:
        candidates = [
            "centrality_in",
            "in_centrality",
            "centrality",
            "in_degree_centrality",
            "centrality_in_degree",
            "centrality (in)",
            "centrality (out)",
            "eigen_centrality",
            "pagerank",
        ]
        for col in candidates:
            if col in df.columns:
                return col
        return None

    def _extract_centrality_metrics(self, values: Optional[Dict]) -> Dict[str, float]:
        metrics: Dict[str, float] = {}
        if not values:
            return metrics

        for canonical, columns in self._CENTRALITY_COLUMN_MAP.items():
            for column in columns:
                if column in values and values[column] is not None:
                    metrics[canonical] = self._safe_float(values[column])
                    break
        return metrics

    def _select_citation_count_column(self, df: pd.DataFrame) -> Optional[str]:
        candidates = [
            "citation_count",
            "citationCount",
            "citedByCount",
            "cited_by_count",
            "numCitations",
            "citations_count",
        ]
        for col in candidates:
            if col in df.columns:
                return col
        return None

    def _get_top_papers(
        self,
        df_results: Optional[pd.DataFrame],
        crawler: Crawler,
        limit: int = 50,
    ) -> List[Dict]:
        if df_results is None or df_results.empty:
            return []

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

        abstract_lookup = {}
        try:
            df_abs = crawler.data_coordinator.frames.df_abstract
            if df_abs is not None and not df_abs.empty:
                abstract_lookup = (
                    df_abs.drop_duplicates(subset=["paperId"])
                    .set_index("paperId")["abstract"]
                    .to_dict()
                )
        except Exception:
            abstract_lookup = {}

        author_lookup = {}
        try:
            df_paper_author = crawler.data_coordinator.frames.df_paper_author
            df_author = crawler.data_coordinator.frames.df_author
            if (
                df_paper_author is not None
                and not df_paper_author.empty
                and df_author is not None
                and not df_author.empty
            ):
                author_map = (
                    df_author.drop_duplicates(subset=["authorId"])
                    .set_index("authorId")["authorName"]
                )
                merged_authors = df_paper_author.merge(
                    author_map.rename("authorName"), on="authorId", how="left"
                )
                author_lookup = (
                    merged_authors.groupby("paperId")["authorName"]
                    .apply(lambda s: [name for name in s.dropna().tolist()])
                    .to_dict()
                )
        except Exception:
            author_lookup = {}

        papers = []
        for _, row in df_sorted.iterrows():
            row_dict = row.to_dict()
            metrics = self._extract_centrality_metrics(row_dict)
            authors_field = row.get("authors", [])
            authors_list: List[str] = []
            if isinstance(authors_field, list) and authors_field:
                if isinstance(authors_field[0], dict):
                    authors_list = [
                        (a.get("name") or a.get("authorName") or "").strip()
                        for a in authors_field
                        if isinstance(a, dict)
                    ]
                else:
                    authors_list = [str(a) for a in authors_field]
            if not authors_list:
                authors_list = author_lookup.get(row["paperId"], [])

            cite_col = self._select_citation_count_column(df_results)
            year_val = row.get("year")
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
            centrality_score = (
                float(row.get(score_col, 0.0)) if score_col else metrics.get("centrality_in", 0.0)
            )

            paper = {
                "paper_id": row["paperId"],
                "title": row.get("title", ""),
                "abstract": row.get("abstract")
                or row.get("paperAbstract", "")
                or abstract_lookup.get(row["paperId"], ""),
                "authors": authors_list,
                "year": year_int,
                "venue": row.get("venue", ""),
                "doi": row.get("doi", ""),
                "citation_count": cite_int,
                "centrality_score": centrality_score,
                "centrality_metrics": metrics,
                "is_seed": bool(row.get("isSeed", False)),
                "is_retracted": bool(row.get("retracted", row.get("isRetracted", False))),
                "url": url_builder.build_url(
                    row["paperId"], crawler.api_config.provider_type
                ),
            }
            papers.append(paper)

        return papers

    def _safe_int(self, value) -> int:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return 0

    def _safe_float(self, value) -> float:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _load_structured_summary(
        self, folder: Optional[Path], name: str
    ) -> Optional[List[Dict]]:
        if not folder:
            return None
        folder_path = Path(folder)
        json_path = folder_path / f"{name}.json"
        if not json_path.exists():
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
        except Exception as exc:
            self.logger.warning("Unable to load structured summary %s: %s", json_path, exc)
        return None

    def _format_authors_from_summary(self, data: List[Dict]) -> List[Dict]:
        formatted = []
        for entry in data:
            formatted.append(
                {
                    "author_id": entry.get("author_id"),
                    "author_name": entry.get("author_name"),
                    "paper_count": self._safe_int(entry.get("paper_count")),
                    "total_citations": self._safe_int(entry.get("num_citations")),
                    "max_citations": self._safe_int(entry.get("max_citations")),
                    "avg_citations": self._safe_float(entry.get("avg_citations")),
                    "centrality_score": self._safe_float(entry.get("centrality_score")),
                }
            )
        return formatted

    def _format_venues_from_summary(self, data: List[Dict]) -> List[Dict]:
        formatted = []
        for entry in data:
            formatted.append(
                {
                    "venue": entry.get("venue"),
                    "venue_id": entry.get("venue_id"),
                    "total_papers": self._safe_int(entry.get("total_papers")),
                    "self_citations": self._safe_int(entry.get("self_citations")),
                    "citing_others": self._safe_int(entry.get("citing_others")),
                    "being_cited_by_others": self._safe_int(
                        entry.get("being_cited_by_others")
                    ),
                }
            )
        return formatted

    def _compute_top_venues(self, data_coord, limit: int = 20) -> List[Dict]:
        df_venues = getattr(data_coord.frames, "df_venue_features", None)
        if df_venues is None or df_venues.empty:
            return []
        segments = []
        for column in [
            "total_papers",
            "self_citations",
            "citing_others",
            "being_cited_by_others",
        ]:
            if column in df_venues.columns:
                segments.append(df_venues.nlargest(5, column))
        if not segments:
            return []
        combined = pd.concat(segments).drop_duplicates(subset=["venue"]).head(limit)
        venues = []
        for _, row in combined.iterrows():
            venues.append(
                {
                    "venue": row.get("venue", ""),
                    "venue_id": row.get("venue_id")
                    or row.get("venueId")
                    or row.get("venue_id_normalized"),
                    "total_papers": self._safe_int(row.get("total_papers")),
                    "self_citations": self._safe_int(row.get("self_citations")),
                    "citing_others": self._safe_int(row.get("citing_others")),
                    "being_cited_by_others": self._safe_int(
                        row.get("being_cited_by_others")
                    ),
                }
            )
        return venues

    def _sort_topic_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        score_col = self._select_centrality_column(df)
        if score_col and score_col in df.columns:
            return df.sort_values(score_col, ascending=False)
        cite_col = self._select_citation_count_column(df)
        if cite_col and cite_col in df.columns:
            return df.sort_values(cite_col, ascending=False)
        return df

    def _get_api_client(self, provider_type: str) -> Optional[BaseAPIProvider]:
        provider = (provider_type or "openalex").lower()
        if provider in self._api_clients:
            return self._api_clients[provider]
        try:
            client = create_api_provider(provider, logger=self.logger)
            self._api_clients[provider] = client
            return client
        except Exception as exc:
            self.logger.error("Unable to initialize API provider %s: %s", provider, exc)
            return None

    def _fetch_provider_metadata(
        self, api_client: BaseAPIProvider, paper_ids: List[str]
    ) -> Dict[str, PaperData]:
        metadata_map: Dict[str, PaperData] = {}

        if hasattr(api_client, "get_papers_batch_as_paper_data"):
            try:
                data_objects = api_client.get_papers_batch_as_paper_data(paper_ids) or {}
                if isinstance(data_objects, dict):
                    iterator = data_objects.items()
                else:
                    iterator = [(None, paper_data) for paper_data in data_objects]

                for pid_key, paper_data in iterator:
                    if not paper_data:
                        continue
                    pid = (
                        self._clean_provider_id(pid_key)
                        if pid_key
                        else self._clean_provider_id(paper_data.paper_id)
                    )
                    if pid:
                        metadata_map[pid] = paper_data

                if metadata_map:
                    return metadata_map
            except Exception as exc:
                self.logger.warning("PaperData batch fetch failed: %s", exc)

        for pid in paper_ids:
            paper_data = None
            try:
                if hasattr(api_client, "get_paper_as_paper_data"):
                    paper_data = api_client.get_paper_as_paper_data(pid)
            except Exception as exc:
                self.logger.debug("Metadata lookup failed for %s: %s", pid, exc)
            if paper_data:
                normalized_id = self._clean_provider_id(paper_data.paper_id)
                if normalized_id:
                    metadata_map[normalized_id] = paper_data

        return metadata_map

    def _clean_provider_id(self, raw_id: Optional[str]) -> Optional[str]:
        if not raw_id:
            return None
        identifier = raw_id.split("/")[-1] if "/" in raw_id else raw_id
        identifier = identifier.strip()
        if not identifier:
            return None
        identifier = identifier.upper()
        if not identifier.startswith("W"):
            identifier = f"W{identifier}"
        return identifier

    def _build_topic_paper_entry(
        self,
        paper_id: str,
        paper_data: Optional[PaperData],
        fallback: Dict,
        provider_type: str,
        url_builder: PaperURLBuilder,
        score_column: Optional[str],
    ) -> Dict:
        fallback = fallback or {}

        title = paper_id
        abstract = None
        authors: List[str] = []
        year: Optional[int] = None
        venue: Optional[str] = None
        doi: Optional[str] = None
        url = url_builder.build_url(paper_id, provider_type)

        if paper_data:
            title = paper_data.title or title
            abstract = paper_data.abstract
            authors = [
                author.get("name") or author.get("authorName")
                for author in paper_data.authors or []
            ]
            authors = [name for name in authors if name]
            year = paper_data.year
            venue = paper_data.venue or paper_data.venue_raw
            doi = paper_data.doi
            url = paper_data.url or url
        else:
            title = fallback.get("title") or fallback.get("paperTitle") or title
            abstract = (
                fallback.get("abstract")
                or fallback.get("paperAbstract")
                or fallback.get("summary")
            )
            authors = fallback.get("authors") or []
            year = fallback.get("year")
            venue = fallback.get("venue")
            doi = fallback.get("doi")
            url = fallback.get("url") or url

        citation_count = None
        for key in [
            "citation_count",
            "citationCount",
            "citedByCount",
            "cited_by_count",
            "numCitations",
            "citations_count",
        ]:
            if fallback.get(key) is not None:
                citation_count = fallback.get(key)
                break
        citation_count = (
            self._safe_int(citation_count) if citation_count is not None else None
        )

        centrality_metrics = self._extract_centrality_metrics(fallback)

        centrality_score = 0.0
        if score_column and score_column in fallback:
            centrality_score = self._safe_float(fallback.get(score_column))
        elif "centrality_in" in centrality_metrics:
            centrality_score = centrality_metrics["centrality_in"]

        is_seed = bool(fallback.get("isSeed") or fallback.get("is_seed"))
        is_retracted = bool(
            fallback.get("retracted")
            or fallback.get("isRetracted")
            or fallback.get("is_retracted")
        )

        return {
            "paper_id": paper_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "year": year,
            "venue": venue,
            "doi": doi,
            "citation_count": citation_count,
            "centrality_score": centrality_score,
            "centrality_metrics": centrality_metrics,
            "is_seed": is_seed,
            "is_retracted": is_retracted,
            "url": url,
        }

    def _build_remote_paper_entry(
        self,
        paper_id: str,
        fallback: Dict,
        provider_type: str,
        url_builder: PaperURLBuilder,
    ) -> Dict:
        return self._build_topic_paper_entry(
            paper_id,
            None,
            fallback,
            provider_type,
            url_builder,
            None,
        )




    def _get_topics_overview(
        self,
        df_results: Optional[pd.DataFrame],
        crawler: Crawler,
    ) -> List[Dict]:
        if df_results is None or df_results.empty:
            return []

        topic_model_type = getattr(
            crawler.text_config, "default_topic_model_type", "NMF"
        )
        topic_col = f"{topic_model_type.lower()}_topic"

        if topic_col not in df_results.columns:
            return []

        topic_results = crawler.text_processor.topicmodeling.results.get(
            topic_model_type.upper(), {}
        )
        top_words_list = topic_results.get("top_words", [])

        topics = []
        topic_counts = df_results[topic_col].value_counts().sort_index()

        for topic_id, count in topic_counts.items():
            if pd.isna(topic_id) or topic_id < 0:
                continue

            topic_id = int(topic_id)

            topic_papers = df_results[df_results[topic_col] == topic_id][
                "paperId"
            ].tolist()

            top_words = []
            if topic_id < len(top_words_list):
                top_words = top_words_list[topic_id]

            topic_label = f"Topic {topic_id}"
            if top_words:
                topic_label = " ".join(top_words[:5])

            topics.append(
                {
                    "topic_id": topic_id,
                    "topic_label": topic_label,
                    "paper_count": int(count),
                    "top_words": top_words,
                    "paper_ids": topic_papers,
                }
            )

        return topics

    def _get_top_authors(
        self,
        df_results: Optional[pd.DataFrame],
        data_coord,
        limit: int = 50,
    ) -> List[Dict]:
        df_author = getattr(data_coord.frames, "df_author", None)
        df_paper_author = getattr(data_coord.frames, "df_paper_author", None)

        if df_author is None or df_author.empty or df_paper_author is None:
            return []

        author_metrics = []

        for _, author_row in df_author.iterrows():
            author_id = author_row["authorId"]

            author_papers = df_paper_author[
                df_paper_author["authorId"] == author_id
            ]["paperId"].tolist()

            if not author_papers:
                continue

            author_df = df_results[df_results["paperId"].isin(author_papers)]
            if author_df.empty:
                continue

            score_col = self._select_centrality_column(author_df)
            centrality = (
                author_df[score_col].mean() if score_col in author_df.columns else 0.0
            )
            cite_col = self._select_citation_count_column(author_df)
            citation = (
                int(author_df[cite_col].sum()) if cite_col in author_df.columns else 0
            )

            author_metrics.append(
                {
                    "author_id": author_id,
                    "author_name": author_row.get("authorName", ""),
                    "paper_count": len(author_papers),
                    "total_citations": citation,
                    "centrality_score": float(centrality or 0),
                }
            )

        author_metrics.sort(key=lambda x: x["centrality_score"], reverse=True)
        return author_metrics[:limit]
