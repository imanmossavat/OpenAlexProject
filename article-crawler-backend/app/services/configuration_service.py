

import logging
from typing import Dict, Optional
from datetime import datetime

from app.schemas.configuration import (
    BasicConfigRequest,
    AdvancedConfigRequest,
    ConfigurationResponse
)
from app.core.exceptions import InvalidInputException


class ConfigurationService:

    
    DEFAULT_IGNORED_VENUES = ["", "ArXiv", "medRxiv", "WWW"]
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
        self._config_storage: Dict[str, Dict] = {}
    
    def initialize_storage(self, session_id: str):
        """Initialize configuration storage for a session if not exists."""
        if session_id not in self._config_storage:
            self._config_storage[session_id] = {
                'basic_config': None,
                'advanced_config': None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
    
    def set_basic_config(
        self,
        session_id: str,
        config: BasicConfigRequest
    ):
        self.initialize_storage(session_id)
        
        self._config_storage[session_id]['basic_config'] = config
        self._config_storage[session_id]['updated_at'] = datetime.now()
        
        self.logger.info(
            f"Set basic config for session {session_id}: "
            f"max_iterations={config.max_iterations}, "
            f"papers_per_iteration={config.papers_per_iteration}"
        )
    
    def set_advanced_config(
        self,
        session_id: str,
        config: AdvancedConfigRequest
    ):

        self.initialize_storage(session_id)
        
        self._config_storage[session_id]['advanced_config'] = config
        self._config_storage[session_id]['updated_at'] = datetime.now()
        
        self.logger.info(
            f"Set advanced config for session {session_id}: "
            f"topic_model={config.topic_model}, num_topics={config.num_topics}"
        )
    
    def get_configuration(self, session_id: str) -> ConfigurationResponse:

        self.initialize_storage(session_id)
        
        storage = self._config_storage[session_id]
        basic = storage['basic_config']
        advanced = storage['advanced_config']
        
        ignored_venues = self.DEFAULT_IGNORED_VENUES.copy()
        if advanced and advanced.additional_ignored_venues:
            ignored_venues.extend(advanced.additional_ignored_venues)
        
        return ConfigurationResponse(
            session_id=session_id,
            has_basic_config=basic is not None,
            has_advanced_config=advanced is not None,
            max_iterations=basic.max_iterations if basic else None,
            papers_per_iteration=basic.papers_per_iteration if basic else None,
            topic_model=advanced.topic_model if advanced else "NMF",
            num_topics=advanced.num_topics if advanced else 20,
            save_figures=advanced.save_figures if advanced else True,
            include_author_nodes=advanced.include_author_nodes if advanced else False,
            enable_retraction_watch=advanced.enable_retraction_watch if advanced else True,
            ignored_venues=ignored_venues if advanced else self.DEFAULT_IGNORED_VENUES,
            language=advanced.language if advanced else "en"
        )
    
    def get_final_config_dict(self, session_id: str) -> Dict:

        self.initialize_storage(session_id)
        
        storage = self._config_storage[session_id]
        basic = storage['basic_config']
        advanced = storage['advanced_config']
        
        if basic is None:
            raise InvalidInputException(
                "Basic configuration not set. Please set basic configuration first."
            )
        
        config_dict = {
            "max_iterations": basic.max_iterations,
            "papers_per_iteration": basic.papers_per_iteration,
            
            "topic_model": advanced.topic_model if advanced else "NMF",
            "num_topics": advanced.num_topics if advanced else 20,
            "save_figures": advanced.save_figures if advanced else True,
            "include_author_nodes": advanced.include_author_nodes if advanced else False,
            "enable_retraction_watch": advanced.enable_retraction_watch if advanced else True,
            "language": advanced.language if advanced else "en",
            
            "ignored_venues": self.DEFAULT_IGNORED_VENUES.copy(),
            
            "api_retries": 3,
            "no_keyword_lambda": 0.2,
            "sampling_hyperparams": {"year": 0.3, "centrality": 1.0},
            "min_abstract_length": 120,
            "stemmer": "Porter",
            "random_state": 42,
            "max_centrality_iterations": 1000,
            "avoid_retraction_in_sampler": False,
            "avoid_retraction_in_reporting": True,
            "log_level": "INFO",
            "open_vault_folder": True
        }
        
        if advanced and advanced.additional_ignored_venues:
            config_dict["ignored_venues"].extend(advanced.additional_ignored_venues)
        
        return config_dict
    
    def clear_configuration(self, session_id: str):

        self.initialize_storage(session_id)
        
        self._config_storage[session_id]['basic_config'] = None
        self._config_storage[session_id]['advanced_config'] = None
        self._config_storage[session_id]['updated_at'] = datetime.now()
        
        self.logger.info(f"Cleared configuration for session {session_id}")
    
    def cleanup_session(self, session_id: str):

        if session_id in self._config_storage:
            del self._config_storage[session_id]
            self.logger.info(f"Cleaned up configuration data for session {session_id}")