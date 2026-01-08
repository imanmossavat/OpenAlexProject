from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.exceptions import InvalidInputException


@dataclass(frozen=True)
class TopicModelingConfig:
    library_path: Path
    model_type: str
    num_topics: int


class TopicModelingConfigBuilder:
    """Validate and construct configuration objects for topic modeling runs."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    def build(self, library_details: Dict, model_type: str, num_topics: int) -> TopicModelingConfig:
        raw_path = (library_details or {}).get("path")
        if not raw_path:
            raise InvalidInputException("Library path is required to run topic modeling.")
        path = Path(str(raw_path))
        if not path.is_absolute():
            raise InvalidInputException("Library path must be an absolute path for topic modeling.")
        self._logger.debug(
            "Building topic modeling config for path=%s, model=%s, num_topics=%s",
            path,
            model_type,
            num_topics,
        )
        return TopicModelingConfig(library_path=path, model_type=model_type, num_topics=num_topics)


class TopicResultRepository:
    """Utility for working with topic modeling artifacts on disk."""

    def __init__(self, topics_dir_name: str = "topics"):
        self._topics_dir_name = topics_dir_name

    def ensure_topics_folder(self, library_path: Path) -> Path:
        folder = library_path / self._topics_dir_name
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def normalize_overview_path(self, overview_path: Optional[Any]) -> Optional[Path]:
        if overview_path is None:
            return None
        return Path(overview_path)


class TopicLabelBuilder:
    """Build human-readable labels for topic clusters."""

    def build(self, cluster: Any) -> str:
        label = getattr(cluster, "label", None)
        if label:
            return str(label)
        topic_id = getattr(cluster, "cluster_id", None)
        return f"Topic {topic_id}" if topic_id is not None else "Untitled Topic"


class TopicResultFormatter:
    """Shape topic modeling clusters into API-friendly payloads."""

    def __init__(self, label_builder: Optional[TopicLabelBuilder] = None):
        self._label_builder = label_builder or TopicLabelBuilder()

    def format(self, clusters: Optional[List[Any]]) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for cluster in clusters or []:
            formatted.append(
                {
                    "topic_id": getattr(cluster, "cluster_id", None),
                    "label": self._label_builder.build(cluster),
                    "paper_ids": list(getattr(cluster, "paper_ids", []) or []),
                }
            )
        return formatted
