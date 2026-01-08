from __future__ import annotations

import logging
from typing import List, Protocol

from ArticleCrawler.api.api_factory import create_api_provider
from ArticleCrawler.pdf_processing.api_matcher import APIMetadataMatcher
from ArticleCrawler.pdf_processing.models import PDFMetadata


class IMetadataMatcher(Protocol):
    """Expected behavior for metadata matching helpers."""

    def match_metadata(self, metadata: List[PDFMetadata]):  # pragma: no cover - protocol
        ...


class IMetadataMatcherFactory(Protocol):
    """Produce matchers for a given provider."""

    def create(self, provider: str) -> IMetadataMatcher:  # pragma: no cover - protocol
        ...


class APIMetadataMatcherAdapter(IMetadataMatcher):
    """Adapter wrapping ArticleCrawler's APIMetadataMatcher."""

    def __init__(self, matcher: APIMetadataMatcher):
        self._matcher = matcher

    def match_metadata(self, metadata: List[PDFMetadata]):
        return self._matcher.match_metadata(metadata)


class APIMetadataMatcherFactory(IMetadataMatcherFactory):
    """Factory returning APIMetadataMatcher adapters per provider."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def create(self, provider: str) -> IMetadataMatcher:
        api = create_api_provider(provider)
        matcher = APIMetadataMatcher(api, logger=self._logger)
        return APIMetadataMatcherAdapter(matcher)
