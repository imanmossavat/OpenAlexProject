from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import ValidationError

from ArticleCrawler.api.api_factory import create_api_provider
from ArticleCrawler.pdf_processing.api_matcher import APIMetadataMatcher
from ArticleCrawler.pdf_processing.models import PDFMetadata

from app.api.dependencies import (
    get_seed_selection_service,
    get_seed_session_service,
    get_staging_service,
)
from app.schemas.seed_session import AddSeedsToSessionResponse
from app.schemas.seeds import MatchedSeed
from app.schemas.staging import (
    BulkRemoveRequest,
    BulkRemoveResponse,
    ColumnCustomFilter,
    ConfirmMatchesRequest,
    MatchSelectedRequest,
    SelectionUpdateRequest,
    SelectionUpdateResponse,
    StagingListResponse,
    StagingMatchResponse,
    StagingMatchRow,
    StagingPaper,
    StagingPaperCreate,
    StagingPaperUpdate,
    NUMBER_FILTER_COLUMNS,
    NUMBER_FILTER_OPERATOR_VALUES,
    TEXT_FILTER_COLUMNS,
    TEXT_FILTER_OPERATOR_VALUES,
)

router = APIRouter()


def _parse_column_filters(raw_filters: Optional[List[str]]) -> List[ColumnCustomFilter]:
    parsed: List[ColumnCustomFilter] = []
    if not raw_filters:
        return parsed

    for raw in raw_filters:
        if not raw:
            continue
        parts = [part.strip() for part in raw.split("::")]
        if len(parts) < 3:
            continue
        column, operator, value = parts[0], parts[1], parts[2]
        value_to = parts[3] if len(parts) > 3 else None
        value_to = value_to or None
        try:
            candidate = ColumnCustomFilter(column=column, operator=operator, value=value, value_to=value_to)
        except ValidationError:
            continue
        if candidate.column in NUMBER_FILTER_COLUMNS:
            if candidate.operator not in NUMBER_FILTER_OPERATOR_VALUES:
                continue
            if candidate.operator in {"between", "not_between"} and not candidate.value_to:
                continue
        else:
            if candidate.operator not in TEXT_FILTER_OPERATOR_VALUES:
                continue
        parsed.append(candidate)
    return parsed


@router.get(
    "/seeds/session/{session_id}/staging",
    response_model=StagingListResponse,
)
async def list_staged_papers(
    session_id: str = Path(..., description="Seed session identifier"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sources: Optional[List[str]] = Query(None, description="Filter by source labels/source types"),
    year_min: Optional[int] = Query(None, description="Minimum publication year"),
    year_max: Optional[int] = Query(None, description="Maximum publication year"),
    title: Optional[str] = Query(None, description="Title search query"),
    venue: Optional[str] = Query(None, description="Venue search query"),
    author: Optional[str] = Query(None, description="Author search query"),
    keyword: Optional[str] = Query(None, description="Keyword search across title and abstract"),
    doi_presence: Optional[str] = Query(
        None,
        description="Filter by DOI presence: 'with' for rows with DOI, 'without' for rows without DOI",
    ),
    title_values: Optional[List[str]] = Query(None, description="Exact match filters for the title column"),
    author_values: Optional[List[str]] = Query(None, description="Exact match filters for the authors column"),
    venue_values: Optional[List[str]] = Query(None, description="Exact match filters for the venue column"),
    year_values: Optional[List[int]] = Query(None, description="Exact match filters for publication year"),
    identifier_values: Optional[List[str]] = Query(
        None,
        description="Identifier filters using 'field::value' format (e.g., 'doi::10.1234/foo')",
    ),
    column_filters: Optional[List[str]] = Query(
        None,
        description="Advanced column filters in the form column::operator::value(::value_to)",
    ),
    selected_only: bool = Query(False, description="Return only selected rows"),
    sort_by: Optional[str] = Query(None, description="Sort column"),
    sort_dir: str = Query("asc", description="Sort direction asc|desc"),
    service=Depends(get_staging_service),
):
    """Return paginated staged papers for a session."""
    identifier_filters: List[Dict[str, str]] = []
    for raw in identifier_values or []:
        if not raw or "::" not in raw:
            continue
        field, value = raw.split("::", 1)
        clean_field = (field or "").strip().lower()
        clean_value = (value or "").strip()
        if not clean_field or not clean_value:
            continue
        if clean_field not in {"doi", "url"}:
            continue
        identifier_filters.append({"field": clean_field, "value": clean_value})
    custom_filters = _parse_column_filters(column_filters)

    return service.list_rows(
        session_id,
        page=page,
        page_size=page_size,
        source_values=sources,
        year_min=year_min,
        year_max=year_max,
        title_search=title,
        venue_search=venue,
        author_search=author,
        keyword_search=keyword,
        doi_presence=doi_presence,
        title_values=title_values,
        author_values=author_values,
        venue_values=venue_values,
        year_values=year_values,
        identifier_filters=identifier_filters,
        custom_filters=custom_filters,
        selected_only=selected_only,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.post(
    "/seeds/session/{session_id}/staging",
    response_model=List[StagingPaper],
)
async def add_staged_papers(
    session_id: str,
    payload: List[StagingPaperCreate],
    staging_service=Depends(get_staging_service),
    seed_selection_service=Depends(get_seed_selection_service),
):
    """Add papers to the staging table."""
    rows_to_add, invalid_manual_ids = await _enrich_manual_metadata(payload, seed_selection_service)
    if not rows_to_add:
        detail = (
            "No valid manual IDs were found."
            if invalid_manual_ids
            else "No rows to add."
        )
        raise HTTPException(status_code=400, detail=detail)
    if invalid_manual_ids:
        staging_service.logger.warning(
            "Skipping %d invalid manual IDs when staging: %s",
            len(invalid_manual_ids),
            ", ".join(invalid_manual_ids[:5]) + ("..." if len(invalid_manual_ids) > 5 else ""),
        )
    return staging_service.add_rows(session_id, rows_to_add)


@router.patch(
    "/seeds/session/{session_id}/staging/{staging_id}",
    response_model=StagingPaper,
)
async def update_staged_paper(
    session_id: str,
    staging_id: int,
    payload: StagingPaperUpdate,
    service=Depends(get_staging_service),
):
    """Inline edit for staged paper row."""
    return service.update_row(session_id, staging_id, payload)


@router.post(
    "/seeds/session/{session_id}/staging/select",
    response_model=SelectionUpdateResponse,
)
async def update_selection(
    session_id: str,
    payload: SelectionUpdateRequest,
    service=Depends(get_staging_service),
):
    """Toggle selection for multiple staged papers."""
    updated = service.set_selection(session_id, payload.staging_ids, payload.is_selected)
    stats = service.list_rows(session_id, page=1, page_size=1)
    return SelectionUpdateResponse(updated_count=updated, selected_count=stats.selected_count)


@router.post(
    "/seeds/session/{session_id}/staging/match",
    response_model=StagingMatchResponse,
)
async def match_selected_rows(
    session_id: str,
    payload: MatchSelectedRequest,
    staging_service=Depends(get_staging_service),
    seed_selection_service=Depends(get_seed_selection_service),
):
    """Match currently selected staged rows using DOI/title heuristics."""
    try:
        selected_rows = staging_service.get_selected_rows(session_id)
        if not selected_rows:
            raise HTTPException(status_code=400, detail="No selected staged papers to match")

        match_rows = await _match_rows_for_items(
            session_id=session_id,
            rows=selected_rows,
            api_provider=payload.api_provider,
            staging_service=staging_service,
            seed_selection_service=seed_selection_service,
        )

        staging_service.store_match_rows(session_id, match_rows)

        matched_rows = [row for row in match_rows if row.matched]
        unmatched_rows = [row for row in match_rows if not row.matched]

        return StagingMatchResponse(
            session_id=session_id,
            total_selected=len(selected_rows),
            matched_rows=matched_rows,
            unmatched_rows=unmatched_rows,
        )
    except HTTPException:
        raise


@router.get(
    "/seeds/session/{session_id}/staging/match",
    response_model=StagingMatchResponse,
)
async def get_last_match_results(
    session_id: str,
    staging_service=Depends(get_staging_service),
):
    """Return the most recent match results for this session."""
    try:
        rows = staging_service.get_match_rows(session_id)
        if not rows:
            raise HTTPException(status_code=404, detail="No match results stored for this session")
        matched_rows = [row for row in rows if row.matched]
        unmatched_rows = [row for row in rows if not row.matched]
        return StagingMatchResponse(
            session_id=session_id,
            total_selected=len(rows),
            matched_rows=matched_rows,
            unmatched_rows=unmatched_rows,
        )
    except HTTPException:
        raise


@router.post(
    "/seeds/session/{session_id}/staging/match/confirm",
    response_model=AddSeedsToSessionResponse,
)
async def confirm_matches(
    session_id: str,
    payload: ConfirmMatchesRequest,
    staging_service=Depends(get_staging_service),
    seed_session_service=Depends(get_seed_session_service),
):
    """Confirm matched rows and persist them as seeds."""
    try:
        rows = staging_service.get_match_rows(session_id)
        if not rows:
            raise HTTPException(status_code=400, detail="Match results not found. Run matching first.")

        allowed_ids = set(payload.staging_ids) if payload.staging_ids else None
        seeds = [
            row.matched_seed
            for row in rows
            if row.matched and row.matched_seed and (allowed_ids is None or row.staging_id in allowed_ids)
        ]

        if not seeds:
            raise HTTPException(status_code=400, detail="No matched seeds to confirm.")

        response = seed_session_service.set_seeds_for_session(session_id, seeds)
        return response
    except HTTPException:
        raise


@router.post(
    "/seeds/session/{session_id}/staging/{staging_id}/rematch",
    response_model=StagingMatchRow,
)
async def rematch_single_row(
    session_id: str,
    staging_id: int,
    payload: MatchSelectedRequest,
    staging_service=Depends(get_staging_service),
    seed_selection_service=Depends(get_seed_selection_service),
):
    """Match a single staged paper after metadata edits."""
    try:
        row = staging_service.get_row(session_id, staging_id)
        match_rows = await _match_rows_for_items(
            session_id=session_id,
            rows=[row],
            api_provider=payload.api_provider,
            staging_service=staging_service,
            seed_selection_service=seed_selection_service,
        )
        if not match_rows:
            raise HTTPException(status_code=400, detail="Unable to match this paper")
        new_row = match_rows[0]
        existing = staging_service.get_match_rows(session_id)
        replaced = False
        for idx, existing_row in enumerate(existing):
            if existing_row.staging_id == staging_id:
                existing[idx] = new_row
                replaced = True
                break
        if not replaced:
            existing.append(new_row)
        staging_service.store_match_rows(session_id, existing)
        return new_row
    except HTTPException:
        raise


@router.delete(
    "/seeds/session/{session_id}/staging/{staging_id}",
    response_model=BulkRemoveResponse,
)
async def delete_staged_paper(
    session_id: str,
    staging_id: int,
    service=Depends(get_staging_service),
):
    """Remove a single staged paper."""
    removed = service.remove_rows(session_id, [staging_id])
    stats = service.list_rows(session_id, page=1, page_size=1)
    return BulkRemoveResponse(removed_count=removed, total_rows=stats.total_rows)


@router.post(
    "/seeds/session/{session_id}/staging/remove",
    response_model=BulkRemoveResponse,
)
async def bulk_remove_staged_papers(
    session_id: str,
    payload: BulkRemoveRequest,
    service=Depends(get_staging_service),
):
    """Remove multiple staged papers."""
    removed = service.remove_rows(session_id, payload.staging_ids)
    stats = service.list_rows(session_id, page=1, page_size=1)
    return BulkRemoveResponse(removed_count=removed, total_rows=stats.total_rows)


@router.delete(
    "/seeds/session/{session_id}/staging",
)
async def clear_staging(
    session_id: str,
    service=Depends(get_staging_service),
):
    """Remove every staged paper for the session."""
    service.clear_session(session_id)
    return {"message": f"Cleared staging for session {session_id}"}


async def _match_rows_for_items(
    session_id: str,
    rows: List[StagingPaper],
    api_provider: str,
    staging_service,
    seed_selection_service,
) -> List[StagingMatchRow]:
    identifiers: Dict[int, str] = {}
    match_methods: Dict[int, str] = {}
    confidences: Dict[int, float] = {}
    unmatched_reasons: Dict[int, str] = {}

    rows_needing_metadata: List[Tuple[StagingPaper, PDFMetadata]] = []
    candidate_ids: List[str] = []

    for row in rows:
        openalex_id = _normalize_openalex_id(row.source_id) or _normalize_openalex_id(row.url)
        if openalex_id:
            identifiers[row.staging_id] = openalex_id
            match_methods[row.staging_id] = "source_id"
            candidate_ids.append(openalex_id)
            continue

        doi = (
            _normalize_doi(row.doi)
            or _normalize_doi(row.source_id)
            or _extract_doi_from_url(row.url)
        )
        metadata = None
        if doi or row.title:
            metadata = PDFMetadata(
                filename=str(row.source_id or row.title or f"staging-{row.staging_id}"),
                title=row.title or "",
                doi=doi,
                year=str(row.year) if row.year is not None else None,
                authors=row.authors,
                venue=row.venue,
            )

        if metadata and (metadata.doi or metadata.title):
            rows_needing_metadata.append((row, metadata))
        else:
            unmatched_reasons[row.staging_id] = "Missing DOI or title for matching"

    if rows_needing_metadata:
        api = create_api_provider(api_provider)
        matcher = APIMetadataMatcher(api, logger=staging_service.logger)
        metadata_results = matcher.match_metadata([meta for _, meta in rows_needing_metadata])

        for (row, meta), result in zip(rows_needing_metadata, metadata_results):
            if result.matched and result.paper_id:
                identifiers[row.staging_id] = result.paper_id
                match_methods[row.staging_id] = result.match_method or ("doi" if meta.doi else "title_search")
                confidences[row.staging_id] = result.confidence
                candidate_ids.append(result.paper_id)
            else:
                reason = result.match_method or "DOI/title search"
                unmatched_reasons[row.staging_id] = f"No match found via {reason.lower()}"

    unique_ids = sorted(set(candidate_ids))
    matched_seeds_by_id: Dict[str, MatchedSeed] = {}
    unmatched_errors: Dict[str, str] = {}

    if unique_ids:
        match_result = seed_selection_service.match_paper_ids(unique_ids, api_provider)
        matched_seeds_by_id = {seed.paper_id: seed for seed in match_result.matched_seeds}
        unmatched_errors = {item.input_id: item.error for item in match_result.unmatched_seeds}

    match_rows: List[StagingMatchRow] = []
    for row in rows:
        staging_id = row.staging_id
        target_id = identifiers.get(staging_id)

        if target_id and target_id in matched_seeds_by_id:
            seed = matched_seeds_by_id[target_id]
            match_rows.append(
                StagingMatchRow(
                    staging_id=staging_id,
                    staging=row,
                    matched=True,
                    matched_seed=seed,
                    match_method=match_methods.get(staging_id),
                    confidence=confidences.get(staging_id),
                )
            )
        else:
            error = unmatched_reasons.get(staging_id)
            if target_id and not error:
                error = unmatched_errors.get(target_id, "Paper metadata not found in provider")
            match_rows.append(
                StagingMatchRow(
                    staging_id=staging_id,
                    staging=row,
                    matched=False,
                    match_method=match_methods.get(staging_id),
                    confidence=confidences.get(staging_id),
                    error=error or "Unable to match this paper",
                )
            )

    return match_rows


async def _enrich_manual_metadata(
    rows: List[StagingPaperCreate], seed_selection_service
) -> tuple[List[StagingPaperCreate], List[str]]:
    """Fetch metadata for manual IDs so staged rows are usable."""
    enriched_rows: List[StagingPaperCreate] = []
    invalid_manual_ids: List[str] = []

    for row in rows or []:
        if row.source_type != "manual":
            enriched_rows.append(row)
            continue

        label = (row.source or "").strip()
        if not label or label.lower() in {"manual", "manual ids", "manual id", "manual papers"}:
            label = "Manual IDs"
        row.source = label

        identifier = row.doi or row.source_id or row.url
        identifier_for_error = identifier or row.source_id or "unknown"

        if not identifier:
            invalid_manual_ids.append(str(identifier_for_error))
            continue

        try:
            match_result = seed_selection_service.match_paper_ids([identifier], api_provider="openalex")
        except Exception:
            invalid_manual_ids.append(str(identifier_for_error))
            continue

        if not match_result.matched_seeds:
            invalid_manual_ids.append(str(identifier_for_error))
            continue

        seed = match_result.matched_seeds[0]
        row.title = row.title or seed.title
        row.authors = row.authors or seed.authors
        row.year = row.year or seed.year
        row.venue = row.venue or seed.venue
        row.doi = row.doi or seed.doi
        row.url = row.url or seed.url
        row.abstract = row.abstract or seed.abstract
        if seed.paper_id and not _normalize_openalex_id(row.source_id or ""):
            row.source_id = seed.paper_id

        enriched_rows.append(row)

    return enriched_rows, invalid_manual_ids


def _normalize_openalex_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if "openalex.org" in raw:
        raw = raw.split("/")[-1]
    raw = raw.strip()
    if not raw:
        return None
    if raw[0].lower() == "w":
        suffix = raw[1:]
        if suffix.isdigit():
            return f"W{suffix}"
    return None


def _normalize_doi(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    raw = raw.replace("https://doi.org/", "").replace("http://doi.org/", "")
    raw = raw.replace("DOI:", "").replace("doi:", "")
    raw = raw.strip()
    if raw.startswith("10."):
        return raw
    return None


def _extract_doi_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if "doi.org/" in url:
        parts = url.split("doi.org/")
        if len(parts) > 1:
            doi = parts[1].split("?")[0]
            return doi.strip()
    return None
