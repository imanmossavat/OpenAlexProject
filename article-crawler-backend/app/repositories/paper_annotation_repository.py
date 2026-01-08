from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any, List, TYPE_CHECKING

import polars as pl
import yaml

from .paper_catalog_repository import _job_directory

if TYPE_CHECKING:
    from app.services.paper_metadata_service import PaperMetadataService


class PaperAnnotationRepository:
    """Handles persistence of user annotations (marks) per crawler job."""

    def __init__(
        self,
        articlecrawler_path: str,
        logger: Optional[logging.Logger] = None,
        metadata_service: Optional["PaperMetadataService"] = None,
    ):
        if not articlecrawler_path:
            raise ValueError("articlecrawler_path must be configured")
        self._root = Path(articlecrawler_path)
        self._logger = logger or logging.getLogger(__name__)
        self._metadata_service = metadata_service

    def load_marks(self, job_id: str) -> Dict[str, str]:
        """Load the mark dictionary for the given job."""
        path = self._annotations_path(job_id)
        if not path.exists():
            self._logger.debug("No annotations store found for job %s at %s", job_id, path)
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle) or {}
                return {str(k): str(v) for k, v in data.items()}
        except Exception as exc:
            self._logger.error("Failed to load annotations for %s: %s", job_id, exc)
            raise

    def save_mark(self, job_id: str, paper_id: str, mark: str) -> Dict[str, str]:
        """
        Persist a mark update for a paper. Returns the updated mapping.

        Passing mark="standard" removes the explicit entry (falling back to default).
        """
        annotations_dir = self._annotations_dir(job_id)
        annotations_dir.mkdir(parents=True, exist_ok=True)
        path = annotations_dir / "paper_marks.json"
        marks = self.load_marks(job_id)
        if mark == "standard":
            marks.pop(paper_id, None)
        else:
            marks[paper_id] = mark
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(marks, handle, ensure_ascii=False, indent=2)
        except Exception as exc:
            self._logger.error("Failed to save annotation for %s in %s: %s", paper_id, job_id, exc)
            raise
        try:
            self._ensure_markdown_note(job_id, paper_id, mark)
            self._sync_markdown_annotation(job_id, paper_id, mark)
        except Exception as exc:
            self._logger.warning("Saved annotation but failed to sync markdown for %s/%s: %s", job_id, paper_id, exc)
        return marks

    def _annotations_path(self, job_id: str) -> Path:
        return self._annotations_dir(job_id) / "paper_marks.json"

    def _annotations_dir(self, job_id: str) -> Path:
        experiments_root = self._root / "experiments"
        job_dir = _job_directory(experiments_root, job_id)
        crawler_dir = job_dir / f"crawler_{job_id}"
        return crawler_dir / "vault" / "annotations"

    def _paper_markdown_path(self, job_id: str, paper_id: str) -> Path:
        experiments_root = self._root / "experiments"
        job_dir = _job_directory(experiments_root, job_id)
        crawler_dir = job_dir / f"crawler_{job_id}"
        return crawler_dir / "vault" / "papers" / f"{paper_id}.md"

    def _markdown_catalog_path(self, job_id: str) -> Path:
        experiments_root = self._root / "experiments"
        job_dir = _job_directory(experiments_root, job_id)
        crawler_dir = job_dir / f"crawler_{job_id}"
        return crawler_dir / "vault" / "parquet" / "papers.parquet"

    def _ensure_markdown_note(self, job_id: str, paper_id: str, mark: str) -> None:
        note_path = self._paper_markdown_path(job_id, paper_id)
        if note_path.exists():
            return
        note_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = self._lookup_catalog_metadata(job_id, paper_id) or {}
        enriched = self._ensure_metadata_completeness(paper_id, metadata)
        if not enriched:
            self._logger.warning("Cannot create markdown note for %s/%s – metadata unavailable", job_id, paper_id)
            return
        content = self._render_note_content(job_id, enriched, mark)
        note_path.write_text(content, encoding="utf-8")

    def _lookup_catalog_metadata(self, job_id: str, paper_id: str) -> Optional[Dict[str, Any]]:
        catalog_path = self._markdown_catalog_path(job_id)
        if not catalog_path.exists():
            return None
        try:
            lf = (
                pl.scan_parquet(str(catalog_path))
                .filter(pl.col("paperId") == paper_id)
                .limit(1)
            )
            df = lf.collect()
        except Exception as exc:
            self._logger.warning("Failed to read catalog metadata for %s/%s: %s", job_id, paper_id, exc)
            return None
        if df.height == 0:
            return None
        return df.to_dicts()[0]

    def _ensure_metadata_completeness(self, paper_id: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ensure we have at least title/abstract/authors by optionally fetching provider data.
        """
        if metadata and metadata.get("abstract") and metadata.get("authors"):
            return metadata
        provider = self._fetch_provider_metadata(paper_id)
        if not provider:
            return metadata or None
        merged = dict(metadata or {})
        merged.setdefault("paperId", provider.get("paper_id"))
        merged["title"] = provider.get("title") or merged.get("title")
        merged["abstract"] = provider.get("abstract") or merged.get("abstract")
        merged["authors"] = provider.get("authors") or merged.get("authors")
        merged["year"] = provider.get("year") or merged.get("year")
        merged["venue"] = provider.get("venue") or merged.get("venue")
        merged["doi"] = provider.get("doi") or merged.get("doi")
        merged["url"] = provider.get("url") or merged.get("url")
        merged["concepts"] = merged.get("concepts") or []
        merged["topics"] = merged.get("topics") or []
        merged["fields"] = merged.get("fields") or []
        merged["subfields"] = merged.get("subfields") or []
        merged["domains"] = merged.get("domains") or []
        return merged

    def _render_note_content(self, job_id: str, metadata: Dict[str, Any], mark: str) -> str:
        paper_id = str(metadata.get("paperId") or metadata.get("paper_id") or "")
        title = metadata.get("title") or paper_id or "Untitled"
        venue = metadata.get("venue")
        year = metadata.get("year")
        doi = metadata.get("doi")
        abstract = metadata.get("abstract") or ""
        url = metadata.get("url") or (f"https://openalex.org/{paper_id}" if paper_id else "")
        authors_structured = self._normalize_authors(metadata.get("authors") or metadata.get("author_names"))
        frontmatter = {
            "paper_id": paper_id,
            "openalex_id": paper_id,
            "title": title,
            "doi": doi,
            "venue": venue,
            "year": year,
            "abstract": abstract,
            "authors": authors_structured,
            "url": url,
            "concepts": self._normalize_structured_metadata(metadata.get("concepts")),
            "topics": self._normalize_structured_metadata(metadata.get("topics")),
            "subfields": self._normalize_structured_metadata(metadata.get("subfields")),
            "fields": self._normalize_structured_metadata(metadata.get("fields")),
            "domains": self._normalize_structured_metadata(metadata.get("domains")),
            "job": {"id": job_id, "experiment": job_id},
            "is_seed": bool(metadata.get("isSeed")),
            "is_selected": bool(metadata.get("selected")),
            "is_key_author": bool(metadata.get("isKeyAuthor")),
            "processed": bool(metadata.get("processed")),
            "retracted": bool(metadata.get("retracted")),
            "annotation": {"status": mark, "updated_at": datetime.now(timezone.utc).isoformat()},
            "notes": [],
            "run_file": "../run.md",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        frontmatter_text = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
        author_names = [a.get("name") for a in authors_structured if a.get("name")]
        body = self._render_note_body(title, url, author_names, venue, year, doi, abstract, paper_id, mark, frontmatter)
        return f"---\n{frontmatter_text}\n---\n\n{body}"

    def _render_note_body(
        self,
        title: str,
        url: str,
        authors: List[str],
        venue: Optional[str],
        year: Optional[Any],
        doi: Optional[str],
        abstract: str,
        paper_id: str,
        mark: str,
        metadata: Dict[str, Any],
    ) -> str:
        header = f"# [{title}]({url})\n\n" if url else f"# {title}\n\n"
        info_lines = ["> [!info] Paper Info"]
        if authors:
            info_lines.append(f"> **Authors:** {', '.join(authors)}  ")
        info_tokens = []
        if year:
            info_tokens.append(f"**Year:** {year}")
        if venue:
            info_tokens.append(f"**Venue:** {venue}")
        if info_tokens:
            info_lines.append("> " + " | ".join(info_tokens) + "  ")
        if doi:
            info_lines.append(f"> **DOI:** [{doi}](https://doi.org/{doi})  ")
        if paper_id:
            openalex_url = f"https://openalex.org/{paper_id}"
            info_lines.append(f"> **OpenAlex:** [{paper_id}]({openalex_url})")
        info_block = "\n".join(info_lines) + "\n\n"
        research_context = self._build_research_context_callout(metadata)
        note_link = (
            f"> [!note] My Notes\n> This paper's note can be found here:  \n> [[notes/{paper_id}_Notes]]\n"
            if paper_id
            else "> [!note] My Notes\n> No notes recorded yet.\n"
        )
        return (
            f"{header}{info_block}## Abstract\n\n{abstract or '*No abstract available*'}\n\n---\n\n"
            f"{research_context}## Annotation\n\n*Status:* {mark}\n\n## Notes\n\n{note_link}"
        )

    def _build_research_context_callout(self, metadata: Dict[str, Any]) -> str:
        lines = ["> [!abstract] Research Context"]
        added = False
        concepts = self._format_structured_names(metadata.get("concepts"), limit=6, separator=" • ")
        if concepts:
            lines.append(f"> **Top Concepts:** {concepts}")
            added = True
        fields = self._format_structured_names(metadata.get("fields"), limit=5)
        if fields:
            lines.append(f"> **Fields:** {fields}")
            added = True
        subfields = self._format_structured_names(metadata.get("subfields"), limit=5)
        if subfields:
            lines.append(f"> **Subfields:** {subfields}")
            added = True
        domains = self._format_structured_names(metadata.get("domains"), limit=5)
        if domains:
            lines.append(f"> **Domains:** {domains}")
            added = True
        if not added:
            lines.append("> Structured metadata not available.")
        lines.append("")
        return "\n".join(lines)

    def _normalize_authors(self, authors_source: Any) -> List[Dict[str, Optional[str]]]:
        authors: List[Dict[str, Optional[str]]] = []
        if not authors_source:
            return authors
        if isinstance(authors_source, str):
            for name in [part.strip() for part in authors_source.split(",") if part.strip()]:
                authors.append({"id": None, "name": name})
            return authors
        if isinstance(authors_source, list):
            for entry in authors_source:
                if isinstance(entry, dict):
                    author_id = entry.get("authorId") or entry.get("id")
                    display = entry.get("name") or entry.get("display_name")
                    if display:
                        authors.append({"id": author_id, "name": display})
                else:
                    display = str(entry).strip()
                    if display:
                        authors.append({"id": None, "name": display})
        return authors

    def _normalize_structured_metadata(self, value: Any) -> List[Dict[str, Any]]:
        if not value:
            return []
        normalized = []
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    normalized.append(item)
                elif hasattr(item, "__dict__"):
                    normalized.append(dict(item.__dict__))
        return normalized

    def _format_structured_names(self, items: Any, limit: int, separator: str = ", ") -> str:
        if not items:
            return ""
        names = []
        for item in items[:limit]:
            if isinstance(item, dict):
                name = item.get("display_name") or item.get("name")
            elif hasattr(item, "display_name"):
                name = getattr(item, "display_name", None)
            else:
                name = str(item)
            if name:
                names.append(name)
        return separator.join(names)

    def _fetch_provider_metadata(self, paper_id: str) -> Optional[Dict[str, Any]]:
        if not self._metadata_service:
            return None
        try:
            detail = self._metadata_service.get_paper_details(paper_id)
        except Exception as exc:
            self._logger.warning("Unable to fetch provider metadata for %s: %s", paper_id, exc)
            return None
        data = detail.dict()
        data["paper_id"] = data.get("paper_id") or paper_id
        return data

    def _sync_markdown_annotation(self, job_id: str, paper_id: str, mark: str) -> None:
        note_path = self._paper_markdown_path(job_id, paper_id)
        if not note_path.exists():
            self._logger.debug("Markdown note not found for %s/%s, skipping annotation sync", job_id, paper_id)
            return
        content = note_path.read_text(encoding="utf-8")
        normalized = content.replace("\r\n", "\n")
        frontmatter_text, body = self._split_frontmatter(normalized)
        if frontmatter_text is None:
            self._logger.debug("No frontmatter detected for %s/%s, skipping annotation sync", job_id, paper_id)
            return
        metadata = yaml.safe_load(frontmatter_text) or {}
        annotation_block = metadata.get("annotation") or {}
        annotation_block["status"] = mark
        annotation_block["updated_at"] = datetime.now(timezone.utc).isoformat()
        metadata["annotation"] = annotation_block
        updated_body = self._replace_annotation_section(body, mark)
        new_frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).strip()
        updated_content = f"---\n{new_frontmatter}\n---\n{updated_body}"
        note_path.write_text(updated_content, encoding="utf-8")

    def _split_frontmatter(self, text: str) -> tuple[Optional[str], str]:
        if not text.startswith("---\n"):
            return None, text
        closing_marker = "\n---\n"
        closing = text.find(closing_marker, 4)
        if closing == -1:
            return None, text
        frontmatter = text[4:closing]
        body = text[closing + len(closing_marker) :]
        return frontmatter, body

    def _replace_annotation_section(self, body: str, mark: str) -> str:
        marker = "\n## "
        section_header = "## Annotation"
        start = body.find(section_header)
        if start == -1:
            return body
        next_section = body.find(marker, start + len(section_header))
        if next_section == -1:
            next_section = len(body)
        new_block = f"{section_header}\n\n*Status:* {mark}\n\n"
        return body[:start] + new_block + body[next_section:]
