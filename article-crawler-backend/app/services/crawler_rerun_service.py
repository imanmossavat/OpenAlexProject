from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from app.core.exceptions import InvalidInputException, LibraryNotFoundException
from app.repositories.experiment_repository import (
    ExperimentConfigRepository,
    StoredExperiment,
)
from app.schemas.configuration import AdvancedConfigRequest, BasicConfigRequest
from app.schemas.crawler_rerun import ExperimentSummary
from app.schemas.seeds import MatchedSeed
from app.services.configuration_service import ConfigurationService
from app.services.integration_settings_service import IntegrationSettingsService
from app.services.keyword.service import KeywordService
from app.services.library.service import LibraryService
from app.services.seeds.session_service import SeedSessionService


class CrawlerRerunService:
    """Coordinate listing experiments and hydrating sessions for reruns."""

    def __init__(
        self,
        *,
        logger: Optional[logging.Logger] = None,
        experiment_repository: ExperimentConfigRepository,
        keyword_service: KeywordService,
        configuration_service: ConfigurationService,
        seed_session_service: SeedSessionService,
        library_service: LibraryService,
        settings_service: IntegrationSettingsService,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._repository = experiment_repository
        self._keyword_service = keyword_service
        self._configuration_service = configuration_service
        self._seed_session_service = seed_session_service
        self._library_service = library_service
        self._settings_service = settings_service

    def list_experiments(
        self,
        *,
        page: int,
        page_size: int,
        query: Optional[str] = None,
    ) -> Tuple[int, List[ExperimentSummary], Optional[str]]:
        root_path = self._current_root()
        entries = self._repository.list_experiments(base_path=root_path)
        normalized_query = query.lower().strip() if isinstance(query, str) else None
        if normalized_query:
            entries = [
                entry
                for entry in entries
                if self._matches_query(entry, normalized_query)
            ]
        entries.sort(key=lambda record: record.updated_at, reverse=True)
        total = len(entries)
        start = max((page - 1) * page_size, 0)
        end = start + page_size
        summaries = [self._to_summary(record) for record in entries[start:end]]
        return total, summaries, root_path

    def load_into_session(self, job_id: str, session_id: str) -> ExperimentSummary:
        self._ensure_rerun_session(session_id)
        root_path = self._current_root()
        experiment = self._repository.get_experiment(job_id, base_path=root_path)
        return self._apply_config_to_session(session_id, experiment)

    def load_from_path(self, session_id: str, experiment_path: str) -> ExperimentSummary:
        self._ensure_rerun_session(session_id)
        experiment = self._repository.load_from_path(experiment_path)
        return self._apply_config_to_session(session_id, experiment)

    def _apply_config_to_session(self, session_id: str, experiment: StoredExperiment) -> ExperimentSummary:
        config = experiment.config

        seeds = [
            MatchedSeed(
                paper_id=paper_id,
                source="crawler_rerun",
                source_type="crawler",
                source_id=experiment.job_id,
            )
            for paper_id in config.seeds
            if paper_id
        ]
        if not seeds:
            raise InvalidInputException(f"Experiment {experiment.job_id} did not contain any seed paper IDs.")
        self._seed_session_service.set_seeds_for_session(session_id, seeds)

        self._keyword_service.set_keywords(session_id, list(config.keywords or []))

        self._configuration_service.clear_configuration(session_id)
        self._configuration_service.set_basic_config(
            session_id,
            BasicConfigRequest(
                max_iterations=config.max_iterations,
                papers_per_iteration=config.papers_per_iteration,
            ),
        )

        additional_venues = self._additional_venues(config.ignored_venues or [])
        self._configuration_service.set_advanced_config(
            session_id,
            AdvancedConfigRequest(
                topic_model=config.topic_model,
                num_topics=config.num_topics,
                save_figures=config.save_figures,
                include_author_nodes=config.include_author_nodes,
                enable_retraction_watch=config.enable_retraction_watch,
                additional_ignored_venues=additional_venues,
                language=config.language,
            ),
        )

        experiment_name = config.display_name or config.name
        if experiment_name:
            self._configuration_service.set_experiment_name(session_id, experiment_name)

        if config.library_path:
            self._ensure_library_details(session_id, config.library_path, config.library_name)

        self._logger.info("Session %s hydrated from experiment %s", session_id, experiment.job_id)
        return self._to_summary(experiment)

    def _matches_query(self, record: StoredExperiment, query: str) -> bool:
        if query in record.job_id.lower():
            return True
        if record.config.display_name and query in record.config.display_name.lower():
            return True
        if record.config.name and query in record.config.name.lower():
            return True
        return False

    def _to_summary(self, record: StoredExperiment) -> ExperimentSummary:
        config = record.config
        return ExperimentSummary(
            job_id=record.job_id,
            name=config.name,
            display_name=config.display_name,
            total_seeds=len(config.seeds or []),
            total_keywords=len(config.keywords or []),
            library_path=str(config.library_path) if config.library_path else None,
            library_name=config.library_name,
            updated_at=record.updated_at,
        )

    def _additional_venues(self, venues: List[str]) -> List[str]:
        defaults = set(ConfigurationService.DEFAULT_IGNORED_VENUES)
        extras: List[str] = []
        for venue in venues:
            normalized = venue or ""
            if normalized in defaults:
                continue
            extras.append(normalized)
        return extras

    def _ensure_library_details(
        self,
        session_id: str,
        library_path: Path,
        library_name: Optional[str],
    ) -> None:
        name = library_name or library_path.name
        try:
            self._library_service.set_details(
                session_id=session_id,
                name=name,
                path=str(library_path),
                description=None,
            )
        except (InvalidInputException, LibraryNotFoundException) as exc:
            raise InvalidInputException(
                f"Unable to load library path '{library_path}' for rerun session: {exc}"
            )

    def _current_root(self) -> Optional[str]:
        settings = self._settings_service.get_experiment_root()
        return settings.path

    def _ensure_rerun_session(self, session_id: str) -> None:
        session = self._seed_session_service.get_session(session_id)
        if session.use_case != "crawler_rerun":
            raise InvalidInputException(
                "Session must be started with use_case='crawler_rerun' to load experiments."
            )
