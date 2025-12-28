from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import yaml


@dataclass
class TopicVisualizationMetadata:
    """Metadata describing a generated topic visualization."""

    model_type: Optional[str] = None
    figure_kind: Optional[str] = None
    description: Optional[str] = None
    note_id: Optional[str] = None


class TopicCompanionWriter:
    """Writes Markdown companions for topic visualization artifacts."""

    def __init__(self, topics_folder: Path, job_id: str, run_file: str = "../run.md"):
        self.topics_folder = Path(topics_folder)
        self.topics_folder.mkdir(parents=True, exist_ok=True)
        self.job_id = job_id
        self.run_file = run_file

    def write_topic_note(
        self,
        title: str,
        image_path: Path,
        metadata: TopicVisualizationMetadata,
    ) -> Path:
        """Create/update a Markdown note referencing the visualization image."""
        note_stem = metadata.note_id or image_path.stem
        note_slug = self._slugify(note_stem)
        note_path = self.topics_folder / f"{note_slug}.md"
        relative_image = self._relative_image_path(image_path)
        yaml_payload = {
            "job_id": self.job_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "type": "topic_visualization",
            "model_type": metadata.model_type,
            "figure_kind": metadata.figure_kind,
            "image": relative_image,
            "run_file": self.run_file,
        }
        yaml_content = yaml.safe_dump(
            {k: v for k, v in yaml_payload.items() if v is not None},
            sort_keys=False,
            allow_unicode=True,
        ).strip()
        body_lines = [
            f"# {title}",
            "",
            metadata.description or "",
            "",
            f"![[{relative_image}]]",
            "",
        ]
        note_path.write_text(f"---\n{yaml_content}\n---\n\n" + "\n".join(body_lines), encoding="utf-8")
        return note_path

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower())
        return slug or "topic"

    def _relative_image_path(self, image_path: Path) -> str:
        rel = os.path.relpath(Path(image_path), self.topics_folder)
        return rel.replace("\\", "/")
