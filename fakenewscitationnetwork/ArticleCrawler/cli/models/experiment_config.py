"""
Experiment configuration model.

Uses Pydantic for validation and serialization.
"""

from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import Optional, Dict, List


class ExperimentConfig(BaseModel):
    """
    Complete experiment configuration.
    
    Matches the configuration structure from demo.py with sensible defaults.
    """
    
    # Core settings
    name: str = Field(..., description="Experiment name")
    seeds: List[str] = Field(..., description="List of seed paper IDs")
    keywords: List[str] = Field(default_factory=list, description="Keyword filters")
    
    # Crawling settings
    max_iterations: int = Field(default=1, ge=1, description="Maximum crawler iterations")
    papers_per_iteration: int = Field(default=1, ge=1, description="Papers to sample per iteration")
    
    # API settings
    api_provider: str = Field(default="openalex", description="API provider (openalex or semantic_scholar)")
    api_retries: int = Field(default=3, ge=0, description="Number of API retry attempts")
    
    # Sampling configuration
    no_keyword_lambda: float = Field(default=0.2, ge=0.0, description="Lambda for exponential decay in sampling")
    sampling_hyperparams: Dict[str, float] = Field(
        default_factory=lambda: {"year": 0.3, "centrality": 1.0},
        description="Hyperparameters for sampling probability"
    )
    ignored_venues: List[str] = Field(
        default_factory=lambda: ["", "ArXiv", "medRxiv", "WWW"],
        description="Venues to ignore in sampling"
    )
    
    # Text processing configuration
    min_abstract_length: int = Field(default=120, ge=0, description="Minimum abstract length")
    num_topics: int = Field(default=20, ge=2, description="Number of topics for topic modeling")
    topic_model: str = Field(default="NMF", description="Topic modeling algorithm (NMF or LDA)")
    stemmer: str = Field(default="Porter", description="Stemmer to use (Porter or None)")
    language: str = Field(default="en", description="Language for text processing")
    save_figures: bool = Field(default=True, description="Whether to save generated figures")
    random_state: int = Field(default=42, description="Random state for reproducibility")
    
    # Graph configuration
    include_author_nodes: bool = Field(default=False, description="Include author nodes in graph")
    max_centrality_iterations: int = Field(default=1000, ge=1, description="Max iterations for centrality calculation")
    
    # Retraction configuration
    enable_retraction_watch: bool = Field(default=True, description="Enable retraction watch")
    avoid_retraction_in_sampler: bool = Field(default=False, description="Avoid retracted papers in sampling")
    avoid_retraction_in_reporting: bool = Field(default=True, description="Avoid retracted papers in reporting")
    
    # Output configuration
    root_folder: Optional[Path] = Field(default=None, description="Root folder for experiments")
    log_level: str = Field(default="INFO", description="Logging level")
    open_vault_folder: bool = Field(default=True, description="Open vault folder after completion")
    
    @field_validator('api_provider')
    @classmethod
    def validate_api_provider(cls, v):
        """Validate API provider choice."""
        valid_providers = ['openalex', 'semantic_scholar', 's2']
        if v.lower() not in valid_providers:
            raise ValueError(f"api_provider must be one of {valid_providers}")
        return v.lower()
    
    @field_validator('topic_model')
    @classmethod
    def validate_topic_model(cls, v):
        """Validate topic model choice."""
        valid_models = ['NMF', 'LDA']
        if v.upper() not in valid_models:
            raise ValueError(f"topic_model must be one of {valid_models}")
        return v.upper()
    
    def to_crawler_configs(self):
        """
        Convert to ArticleCrawler configuration objects.
        
        Returns:
            Dictionary of configuration objects for Crawler initialization
        """
        from ArticleCrawler.config import (
            APIConfig, SamplingConfig, TextProcessingConfig,
            StorageAndLoggingConfig, GraphConfig, RetractionConfig, StoppingConfig
        )
        
        # Determine root folder
        if self.root_folder is None:
            root_folder = Path.cwd() / 'data' / 'crawler_experiments'
        else:
            root_folder = self.root_folder
        
        return {
            "api_config": APIConfig(
                provider_type=self.api_provider,
                retries=self.api_retries
            ),
            "sampling_config": SamplingConfig(
                num_papers=self.papers_per_iteration,
                no_key_word_lambda=self.no_keyword_lambda,
                hyper_params=self.sampling_hyperparams,
                ignored_venues=self.ignored_venues
            ),
            "text_config": TextProcessingConfig(
                abstract_min_length=self.min_abstract_length,
                num_topics=self.num_topics,
                default_topic_model_type=self.topic_model,
                stemmer=self.stemmer if self.stemmer != "None" else None,
                language=self.language,
                save_figures=self.save_figures,
                random_state=self.random_state
            ),
            "storage_config": StorageAndLoggingConfig(
                experiment_file_name=self.name,
                root_folder=root_folder,
                log_level=self.log_level,
                open_vault_folder=self.open_vault_folder
            ),
            "graph_config": GraphConfig(
                ignored_venues=self.ignored_venues,
                include_author_nodes=self.include_author_nodes,
                max_centrality_iterations=self.max_centrality_iterations
            ),
            "retraction_config": RetractionConfig(
                enable_retraction_watch=self.enable_retraction_watch,
                avoid_retraction_in_sampler=self.avoid_retraction_in_sampler,
                avoid_retraction_in_reporting=self.avoid_retraction_in_reporting
            ),
            "stopping_config": StoppingConfig(
                max_iter=self.max_iterations,
                max_df_size=1E9
            )
        }
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class ConfigBuilder:
    """
    Builder for constructing ExperimentConfig step by step.
    
    Uses Builder pattern for flexible configuration construction.
    """
    
    def __init__(self):
        self._config = {}
        self._apply_defaults()
    
    def _apply_defaults(self):
        """Apply default values matching demo.py."""
        self._config.update({
            "max_iterations": 1,
            "papers_per_iteration": 1,
            "api_provider": "openalex",
            "api_retries": 3,
            "no_keyword_lambda": 0.2,
            "sampling_hyperparams": {"year": 0.3, "centrality": 1.0},
            "ignored_venues": ["", "ArXiv", "medRxiv", "WWW"],
            "min_abstract_length": 120,
            "num_topics": 20,
            "topic_model": "NMF",
            "stemmer": "Porter",
            "language": "en",
            "save_figures": True,
            "random_state": 42,
            "include_author_nodes": False,
            "max_centrality_iterations": 1000,
            "enable_retraction_watch": True,
            "avoid_retraction_in_sampler": False,
            "avoid_retraction_in_reporting": True,
            "log_level": "INFO",
            "open_vault_folder": True,
        })
    
    def with_name(self, name: str) -> "ConfigBuilder":
        """Set experiment name."""
        self._config["name"] = name
        return self
    
    def with_seeds(self, seeds: List[str]) -> "ConfigBuilder":
        """Set seed paper IDs."""
        self._config["seeds"] = seeds
        return self
    
    def with_keywords(self, keywords: List[str]) -> "ConfigBuilder":
        """Set keyword filters."""
        self._config["keywords"] = keywords
        return self
    
    def with_max_iterations(self, max_iter: int) -> "ConfigBuilder":
        """Set maximum iterations."""
        self._config["max_iterations"] = max_iter
        return self
    
    def with_papers_per_iteration(self, num_papers: int) -> "ConfigBuilder":
        """Set papers per iteration."""
        self._config["papers_per_iteration"] = num_papers
        return self
    
    def with_api_provider(self, provider: str) -> "ConfigBuilder":
        """Set API provider."""
        self._config["api_provider"] = provider
        return self
    
    def with_num_topics(self, num_topics: int) -> "ConfigBuilder":
        """Set number of topics."""
        self._config["num_topics"] = num_topics
        return self
    
    def with_topic_model(self, model: str) -> "ConfigBuilder":
        """Set topic modeling algorithm."""
        self._config["topic_model"] = model
        return self
    
    def with_include_author_nodes(self, include: bool) -> "ConfigBuilder":
        """Set whether to include author nodes."""
        self._config["include_author_nodes"] = include
        return self
    
    def with_enable_retraction_watch(self, enable: bool) -> "ConfigBuilder":
        """Set whether to enable retraction watch."""
        self._config["enable_retraction_watch"] = enable
        return self
    
    def with_ignored_venues(self, venues: List[str]) -> "ConfigBuilder":
        """Set ignored venues list."""
        self._config["ignored_venues"] = venues
        return self

    def with_save_figures(self, save: bool) -> "ConfigBuilder":
        """Set whether to save figures."""
        self._config["save_figures"] = save
        return self

    def with_language(self, language: str) -> "ConfigBuilder":
        """Set language for text processing."""
        self._config["language"] = language
        return self
    
    def with_root_folder(self, folder: Path) -> "ConfigBuilder":
        """Set root output folder."""
        self._config["root_folder"] = folder
        return self
    
    def build(self) -> ExperimentConfig:
        """
        Build and validate the final configuration.
        
        Returns:
            ExperimentConfig object
        """
        return ExperimentConfig(**self._config)