import logging
from typing import Any, Dict, List, Optional, Tuple

from ArticleCrawler.api.api_factory import create_api_provider
from ArticleCrawler.api.base_api import BaseAPIProvider

from app.core.exceptions import InvalidInputException
from app.schemas.papers import PaperDetail


class PaperMetadataService:
    """Fetch full metadata for a paper from the configured API provider."""

    def __init__(self, provider: str = "openalex", logger: Optional[logging.Logger] = None):
        self._provider_name = provider
        self._logger = logger or logging.getLogger(__name__)
        self._api: Optional[BaseAPIProvider] = None

    def get_paper_details(self, paper_id: str) -> PaperDetail:
        """Fetch and normalize paper metadata."""
        if not paper_id or not str(paper_id).strip():
            raise InvalidInputException("paper_id is required")

        metadata = self._fetch_metadata(paper_id.strip())
        if not metadata:
            raise InvalidInputException(f"Paper '{paper_id}' was not found in {self._provider_name}.")

        return self._build_response(self._ensure_dict(metadata))

    # Internal helpers -----------------------------------------------------------------

    def _fetch_metadata(self, paper_id: str) -> Optional[Dict[str, Any]]:
        api = self._get_api()
        try:
            if hasattr(api, "get_paper_metadata_only"):
                metadata = api.get_paper_metadata_only(paper_id)
            else:
                metadata = api.get_paper(paper_id)
            return metadata
        except Exception as exc:
            self._logger.error("Error fetching metadata for %s: %s", paper_id, exc)
            return None

    def _build_response(self, metadata: Dict[str, Any]) -> PaperDetail:
        paper_id = self._clean_id(metadata.get("id") or metadata.get("paper_id") or "")
        if not paper_id:
            raise InvalidInputException("Unable to resolve paper identifier from provider response.")

        title = metadata.get("title") or metadata.get("display_name") or paper_id
        abstract = metadata.get("abstract") or self._reconstruct_abstract(metadata.get("abstract_inverted_index"))

        authors, institutions = self._extract_authors_and_institutions(metadata.get("authorships", []))

        venue = None
        primary_location = metadata.get("primary_location") or {}
        if primary_location:
            source = primary_location.get("source") or {}
            venue = source.get("display_name") or venue
        if not venue and metadata.get("host_venue"):
            venue = (metadata["host_venue"] or {}).get("display_name")

        doi = metadata.get("doi") or None
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")

        references = metadata.get("referenced_works")
        references_count = len(references) if isinstance(references, list) else metadata.get("references_count")
        if isinstance(references_count, float):
            references_count = int(references_count)

        cited_by = metadata.get("cited_by_count")
        if isinstance(cited_by, float):
            cited_by = int(cited_by)

        landing_page = primary_location.get("landing_page_url") if isinstance(primary_location, dict) else None
        if not landing_page and metadata.get("best_oa_location"):
            landing_page = (metadata["best_oa_location"] or {}).get("landing_page_url")

        url = landing_page or metadata.get("url") or f"https://openalex.org/{paper_id}"

        return PaperDetail(
            paper_id=paper_id,
            title=title,
            abstract=abstract,
            authors=authors,
            institutions=institutions,
            year=metadata.get("publication_year"),
            venue=venue,
            doi=doi,
            url=url,
            cited_by_count=cited_by if isinstance(cited_by, int) else None,
            references_count=references_count if isinstance(references_count, int) else None,
        )

    def _extract_authors_and_institutions(
        self, authorships: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        authors: List[str] = []
        institutions: List[str] = []
        seen_institutions = set()

        for authorship in authorships or []:
            author = authorship.get("author") or {}
            display_name = author.get("display_name")
            if display_name:
                authors.append(display_name)

            for inst in authorship.get("institutions") or []:
                display = inst.get("display_name") or inst.get("name")
                if display and display not in seen_institutions:
                    seen_institutions.add(display)
                    institutions.append(display)

        return authors, institutions

    def _reconstruct_abstract(self, inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
        if not inverted_index or not isinstance(inverted_index, dict):
            return None
        try:
            positions = []
            for word, indexes in inverted_index.items():
                for pos in indexes:
                    positions.append((pos, word))
            positions.sort(key=lambda item: item[0])
            tokens = [word for _, word in positions]
            reconstructed = " ".join(tokens).strip()
            return reconstructed or None
        except Exception:
            return None

    def _clean_id(self, identifier: str) -> str:
        if not identifier:
            return ""
        if "/" in identifier:
            identifier = identifier.split("/")[-1]
        identifier = identifier.strip()
        if identifier and not identifier.startswith("W") and identifier[0].isdigit():
            identifier = f"W{identifier}"
        return identifier

    def _get_api(self) -> BaseAPIProvider:
        if not self._api:
            self._api = create_api_provider(self._provider_name, logger=self._logger)
        return self._api

    def _ensure_dict(self, metadata: Any) -> Dict[str, Any]:
        if isinstance(metadata, dict):
            return metadata
        if hasattr(metadata, "__dict__"):
            return {
                key: self._coerce_value(value)
                for key, value in metadata.__dict__.items()
            }
        return {}

    def _coerce_value(self, value: Any) -> Any:
        if isinstance(value, list):
            return [self._coerce_value(item) for item in value]
        if hasattr(value, "__dict__"):
            return self._coerce_value(value.__dict__)
        return value
