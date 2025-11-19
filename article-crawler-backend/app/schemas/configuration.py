from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class BasicConfigRequest(BaseModel):
    """Basic crawler configuration."""
    max_iterations: int = Field(default=1, ge=1, description="Maximum crawler iterations")
    papers_per_iteration: int = Field(default=1, ge=1, description="Papers to sample per iteration")


class AdvancedConfigRequest(BaseModel):
    """Advanced crawler configuration (optional)."""
    
    topic_model: str = Field(default="NMF", description="Topic modeling algorithm (NMF or LDA)")
    num_topics: int = Field(default=20, ge=2, le=100, description="Number of topics for topic modeling")
    save_figures: bool = Field(default=True, description="Whether to save topic modeling figures")
    
    include_author_nodes: bool = Field(default=False, description="Include author nodes in citation graph")
    
    enable_retraction_watch: bool = Field(default=True, description="Enable retraction watch checks")
    
    additional_ignored_venues: List[str] = Field(
        default_factory=list,
        description="Additional venues to ignore (beyond defaults: ArXiv, medRxiv, WWW)"
    )
    
    language: str = Field(default="en", description="Language for text processing")
    
    @field_validator('topic_model')
    @classmethod
    def validate_topic_model(cls, v):
        """Validate topic model choice."""
        valid_models = ['NMF', 'LDA']
        if v.upper() not in valid_models:
            raise ValueError(f"topic_model must be one of {valid_models}")
        return v.upper()
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'ru', 'zh', 'ja', 'ar']
        if v.lower() not in valid_languages:
            raise ValueError(
                f"language must be one of {valid_languages}. "
                f"For other languages, ensure they're supported by your text processing library."
            )
        return v.lower()


class ConfigurationResponse(BaseModel):
    """Response showing current configuration."""
    session_id: str
    has_basic_config: bool
    has_advanced_config: bool
    
    max_iterations: Optional[int] = None
    papers_per_iteration: Optional[int] = None
    
    topic_model: Optional[str] = None
    num_topics: Optional[int] = None
    save_figures: Optional[bool] = None
    include_author_nodes: Optional[bool] = None
    enable_retraction_watch: Optional[bool] = None
    ignored_venues: Optional[List[str]] = None
    language: Optional[str] = None


class FinalizeConfigurationResponse(BaseModel):
    """Response after finalizing configuration."""
    session_id: str
    experiment_name: str
    message: str
    
    total_seeds: int
    total_keywords: int
    max_iterations: int
    papers_per_iteration: int
    
    config_summary: dict


class FinalizeConfigurationRequest(BaseModel):
    """Request body for finalizing configuration.

    Supports both seed-session based and library-based flows.
    """
    experiment_name: str = Field(..., description="Name for the experiment")
    library_path: Optional[str] = Field(
        default=None,
        description="Absolute path to an existing library to use for seeds"
    )
    library_name: Optional[str] = Field(
        default=None,
        description="Optional library name (for display/traceability)"
    )
