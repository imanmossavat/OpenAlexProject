from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass(frozen=True)
class CrawlerProgressSnapshot:
    """Normalized progress data emitted by crawler iterations."""

    iterations_completed: int
    iterations_total: int
    papers_collected: int
    seed_papers: int
    citations_collected: int
    references_collected: int
    papers_added_this_iteration: int
    last_update: datetime

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "CrawlerProgressSnapshot":
        """Build a snapshot from a raw dictionary payload."""
        return cls(
            iterations_completed=int(payload.get("iterations_completed", 0)),
            iterations_total=int(payload.get("iterations_total", 0)),
            papers_collected=int(payload.get("papers_collected", 0)),
            seed_papers=int(payload.get("seed_papers", 0)),
            citations_collected=int(payload.get("citations_collected", 0)),
            references_collected=int(payload.get("references_collected", 0)),
            papers_added_this_iteration=int(payload.get("papers_added_this_iteration", 0)),
            last_update=payload.get("timestamp")
            if isinstance(payload.get("timestamp"), datetime)
            else datetime.utcnow(),
        )

    def as_job_updates(self) -> Dict[str, Any]:
        """Convert the snapshot into fields stored on the job record."""
        iterations_total = max(self.iterations_total, 0)
        remaining = max(iterations_total - self.iterations_completed, 0)
        return {
            "current_iteration": self.iterations_completed,
            "iterations_completed": self.iterations_completed,
            "iterations_remaining": remaining,
            "papers_collected": self.papers_collected,
            "seed_papers": self.seed_papers,
            "citations_collected": self.citations_collected,
            "references_collected": self.references_collected,
            "papers_added_this_iteration": self.papers_added_this_iteration,
            "last_progress_at": self.last_update,
        }
