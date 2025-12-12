from __future__ import annotations

import logging
from typing import Optional

from ArticleCrawler.api.api_factory import create_api_provider


class ArticleCrawlerAPIProviderFactory:
    """Factory wrapper for creating ArticleCrawler API provider instances."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    def get_provider(self, provider: str = "openalex"):
        normalized = (provider or "openalex").lower()
        self._logger.debug("Creating API provider for %s", normalized)
        return create_api_provider(normalized)
