import logging
from typing import List, Optional

from app.schemas.seeds import MatchedSeed, SeedMatchResult, UnmatchedSeed
from app.services.seeds.helpers import (
    PaperMetadataFetcher,
    SeedAggregationHelper,
    SeedMatchBuilder,
    SeedMatchClientFactory,
    SeedResultBuilder,
)


class SeedSelectionService:
    """Orchestrate paper-id matching using injected metadata helpers."""

    def __init__(
        self,
        logger: logging.Logger,
        client_factory: Optional[SeedMatchClientFactory] = None,
        metadata_fetcher: Optional[PaperMetadataFetcher] = None,
        match_builder: Optional[SeedMatchBuilder] = None,
        result_builder: Optional[SeedResultBuilder] = None,
        aggregator: Optional[SeedAggregationHelper] = None,
    ):
        self.logger = logger
        self._client_factory = client_factory or SeedMatchClientFactory(logger=logger)
        self._metadata_fetcher = metadata_fetcher or PaperMetadataFetcher(self._client_factory, logger=logger)
        self._match_builder = match_builder or SeedMatchBuilder(logger=logger)
        self._result_builder = result_builder or SeedResultBuilder(self._match_builder, logger=logger)
        self._aggregator = aggregator or SeedAggregationHelper()

    def match_paper_ids(self, paper_ids: List[str], api_provider: str = "openalex") -> SeedMatchResult:
        self.logger.info("Matching %s paper IDs with %s", len(paper_ids), api_provider)
        matched: List[MatchedSeed] = []
        unmatched: List[UnmatchedSeed] = []

        provider = (api_provider or "openalex").lower()
        # warm client
        self._client_factory.get_client(provider)

        for paper_id in paper_ids:
            metadata = self._metadata_fetcher.fetch(provider, paper_id)
            matched_seed, unmatched_seed = self._result_builder.process(provider, paper_id, metadata)
            if matched_seed:
                matched.append(matched_seed)
                self.logger.debug("Matched %s -> %s", paper_id, matched_seed.paper_id)
            if unmatched_seed:
                unmatched.append(unmatched_seed)

        self.logger.info(
            "Matching complete: %s matched, %s unmatched",
            len(matched),
            len(unmatched),
        )
        return SeedMatchResult(
            matched_seeds=matched,
            unmatched_seeds=unmatched,
            total_matched=len(matched),
            total_unmatched=len(unmatched),
        )

    def validate_paper_id(self, paper_id: str) -> bool:
        try:
            from ArticleCrawler.cli.ui.validators import validate_paper_id

            return validate_paper_id(paper_id)
        except ImportError:
            return bool(paper_id and len(paper_id) > 0)

    def aggregate_seeds(self, match_results: List[SeedMatchResult]) -> List[MatchedSeed]:
        aggregated = self._aggregator.aggregate(match_results)
        self.logger.info("Aggregated %s unique seeds from %s sources", len(aggregated), len(match_results))
        return aggregated
