from __future__ import annotations

import logging
from typing import List

from ArticleCrawler.api.zotero.exporter import (
    PaperExportPayload,
    ZoteroExportOptions,
    ZoteroExportService as CoreZoteroExportService,
)

from app.core.exceptions import InvalidInputException
from app.schemas.zotero_export import ZoteroExportRequest, ZoteroExportResponse
from app.services.catalog.service import PaperCatalogService
from app.services.zotero.helpers import ZoteroClientAdapter


class ZoteroExportCoordinator:
    """Coordinates catalog lookups and delegates export logic to ArticleCrawler."""

    def __init__(
        self,
        catalog_service: PaperCatalogService,
        logger: logging.Logger,
        client_adapter: ZoteroClientAdapter | None = None,
    ):
        self._catalog_service = catalog_service
        self._logger = logger
        self._client_adapter = client_adapter or ZoteroClientAdapter(logger=logger)

    def list_collections(self) -> List[dict]:
        """Return all Zotero collections configured for the current credentials."""
        client = self._client_adapter.get_client()
        return client.get_collections()

    def export(self, job_id: str, request: ZoteroExportRequest) -> ZoteroExportResponse:
        """Export the requested job papers to Zotero."""
        summaries = self._catalog_service.get_paper_summaries(job_id, request.paper_ids)
        if not summaries:
            raise InvalidInputException("None of the requested paper IDs were found in the catalog.")

        client = self._client_adapter.get_client()
        export_service = CoreZoteroExportService(logger=self._logger, client=client)

        payloads: List[PaperExportPayload] = []
        for summary in summaries:
            tags = [
                f"mark:{summary.mark}",
            ]
            if summary.is_seed:
                tags.append("seed")
            payloads.append(
                PaperExportPayload(
                    paper_id=summary.paper_id,
                    title=summary.title,
                    authors=summary.authors,
                    year=summary.year,
                    venue=summary.venue,
                    doi=summary.doi,
                    url=summary.url,
                    tags=tags,
                )
            )

        options = ZoteroExportOptions(
            collection_key=request.collection_key,
            collection_name=request.collection_name,
            create_collection=request.create_collection,
            dedupe=request.dedupe,
            extra_tags=request.tags,
        )
        export_result = export_service.export_papers(payloads, options)
        return ZoteroExportResponse(
            created=len(export_result.created),
            skipped=len(export_result.skipped),
            failed=len(export_result.failed),
            created_paper_ids=export_result.created,
            skipped_papers=export_result.skipped,
            failed_papers=export_result.failed,
        )
