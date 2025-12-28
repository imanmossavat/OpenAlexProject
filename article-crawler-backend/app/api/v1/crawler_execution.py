from fastapi import APIRouter, Body, Depends, HTTPException, Path as PathParam, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
import logging
import io

from app.api.dependencies import (
    get_crawler_execution_service, 
    get_seed_session_service,
    get_keyword_service,
    get_configuration_service,
    get_library_service,
    get_paper_catalog_service,
)
from app.schemas.crawler_execution import (
    StartCrawlerRequest,
    StartCrawlerResponse,
    CrawlerStatus,
    CrawlerResults,
    TopicPapersResponse,
    EntityPapersResponse,
)
from app.schemas.papers import (
    PaginatedPaperSummaries,
    ColumnOptionsPage,
    PaperMarkRequest,
    PaperMarkResponse,
)
from app.services.staging.query_parser import StagingQueryParser

router = APIRouter()
logger = logging.getLogger("ArticleCrawlerAPI")


@router.post("/{session_id}/start", response_model=StartCrawlerResponse)
async def start_crawler(
    session_id: str = PathParam(..., description="Session ID"),
    request: StartCrawlerRequest = StartCrawlerRequest(),
    crawler_service = Depends(get_crawler_execution_service),
    session_service = Depends(get_seed_session_service),
    keyword_service = Depends(get_keyword_service),
    config_service = Depends(get_configuration_service),
    library_service = Depends(get_library_service)
):
    """
    Start the crawler with all configuration from the session.
    
    Prerequisites:
    - Session must be finalized
    - Session must have at least one seed
    - Session must have keywords configured
    - Session must have basic and advanced configuration complete
    
    This endpoint starts a background crawler job that:
    1. Executes the citation network crawl
    2. Generates markdown files
    3. Performs topic modeling and analysis
    4. Calculates centrality measures
    
    Returns a job_id that can be used to track progress and retrieve results.
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    req_library_path = getattr(request, "library_path", None)
    using_library = bool(req_library_path)
    selected_details = None
    if not using_library:
        try:
            selected_details = library_service.get_details(session_id)
            if selected_details and selected_details.get("path"):
                using_library = True
        except Exception:
            selected_details = None

    if not using_library:
        if not session.seeds or len(session.seeds) == 0:
            raise HTTPException(
                status_code=400,
                detail="Session must have at least one seed paper or a library_path must be provided"
            )

    experiment_name = config_service.get_experiment_name(session_id)

    session_data = {
        "session_id": session.session_id,
        "use_case": session.use_case,
        "seeds": [seed.model_dump() for seed in session.seeds],
        "keywords": keyword_service.get_keywords(session_id),
        "configuration": config_service.get_final_config_dict(session_id),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
    if experiment_name:
        session_data["experiment_name"] = experiment_name

    if using_library:
        library_path = req_library_path or (selected_details.get("path") if selected_details else None)
        library_name = getattr(request, "library_name", None) or (selected_details.get("name") if selected_details else None)
        if library_path:
            session_data["library_path"] = library_path
        if library_name:
            session_data["library_name"] = library_name

    job_id = crawler_service.start_crawler(
        session_id=session_id,
        session_data=session_data
    )
    
    return StartCrawlerResponse(
        job_id=job_id,
        status="running",
        message=f"Crawler job {job_id} started successfully"
    )


@router.get("/jobs", response_model=List[CrawlerStatus])
async def list_crawler_jobs(
    crawler_service = Depends(get_crawler_execution_service)
):
    """
    List all crawler jobs and their status.
    
    Returns all jobs that have been started, including:
    - Running jobs
    - Completed jobs
    - Failed jobs
    """
    jobs = crawler_service.list_jobs()
    return jobs


@router.get("/jobs/{job_id}/status", response_model=CrawlerStatus)
async def get_crawler_status(
    job_id: str = PathParam(..., description="Job ID"),
    crawler_service = Depends(get_crawler_execution_service)
):
    """
    Get the current status of a crawler job.
    
    Returns:
    - job_id: Job identifier
    - status: running, completed, or failed
    - current_iteration: Current iteration number
    - max_iterations: Maximum iterations configured
    - papers_collected: Total papers collected so far
    - started_at: Job start time
    - completed_at: Job completion time (if completed)
    - error_message: Error message (if failed)
    """
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return status


@router.get("/jobs/{job_id}/results", response_model=CrawlerResults)
async def get_crawler_results(
    job_id: str = PathParam(..., description="Job ID"),
    crawler_service = Depends(get_crawler_execution_service)
):
    """
    Get complete results from a completed crawler job.
    
    This endpoint returns:
    
    **Network Overview:**
    - Total nodes and edges in citation network
    - Number of paper nodes and author nodes
    - Total papers collected
    - Number of iterations completed
    - Number of topics discovered
    - Number of retracted papers detected
    
    **Temporal Distribution:**
    - Papers grouped by publication year
    
    **Top Papers:**
    - Top 50 papers ranked by centrality score
    - Includes metadata, topic assignments, and URLs
    
    **Topics:**
    - All discovered topics with labels
    - Paper counts per topic
    - Top words for each topic
    - Paper IDs in each topic
    
    **Top Authors:**
    - Top 50 authors ranked by average centrality
    - Paper counts and total citations per author
    
    Only available for completed jobs.
    """
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}, results only available for completed jobs"
        )
    
    results = crawler_service.get_results(job_id)
    if not results:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve results for job {job_id}"
        )
    
    return results

@router.get(
    "/jobs/{job_id}/papers",
    response_model=PaginatedPaperSummaries,
    summary="Browse the full paper catalog for a completed job",
)
async def list_job_papers(
    job_id: str = PathParam(..., description="Job ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Rows per page"),
    query: Optional[str] = Query(
        None, description="Filter by title or paper identifier"
    ),
    venue: Optional[str] = Query(None, description="Filter by venue name"),
    doi: Optional[str] = Query(None, description="Filter by DOI substring"),
    year_from: Optional[int] = Query(None, description="Lower bound for publication year"),
    year_to: Optional[int] = Query(None, description="Upper bound for publication year"),
    topic: Optional[int] = Query(
        None, description="Topic number to filter by (matches NMF and LDA unless topic_model is provided)"
    ),
    topic_model: Optional[str] = Query(
        None, description="Topic model to apply (nmf or lda)"
    ),
    topic_ids: Optional[List[int]] = Query(
        None,
        description="Repeatable topic filter (?topic_ids=1&topic_ids=2)",
    ),
    doi_filter: Optional[str] = Query(
        None, description="Filter by DOI presence (with, without, all)"
    ),
    seed_filter: Optional[str] = Query(
        None, description="Filter by seed status (with, without, all)"
    ),
    retraction_filter: Optional[str] = Query(
        None, description="Filter by retraction status (with, without, all)"
    ),
    seed_only: bool = Query(False, description="(Deprecated) Return only seed papers"),
    retracted_only: bool = Query(False, description="(Deprecated) Return only retracted papers"),
    marks: Optional[List[str]] = Query(
        None,
        alias="mark",
        description="Filter by annotation mark (repeatable: ?mark=good&mark=bad)",
    ),
    title_values: Optional[List[str]] = Query(
        None, description="Exact title values selected from the column filter"
    ),
    author_values: Optional[List[str]] = Query(
        None, description="Author names selected from the column filter"
    ),
    venue_values: Optional[List[str]] = Query(
        None, description="Venue names selected from the column filter"
    ),
    year_values: Optional[List[int]] = Query(
        None, description="Publication years selected from the column filter"
    ),
    identifier_filters: Optional[List[str]] = Query(
        None,
        description="Identifier filters using the pattern 'field::value' (e.g. doi::10.1000/xyz)",
    ),
    column_filters: Optional[List[str]] = Query(
        None,
        description="Custom column filters using the format column::operator::value[::value_to]",
    ),
    sort_by: Optional[str] = Query(
        None,
        description="Column to sort by (e.g., title, year, centrality_out). Defaults to backend ordering.",
    ),
    sort_dir: Optional[str] = Query(
        'desc',
        description="Sort direction for sort_by (asc or desc). Defaults to desc.",
    ),
    crawler_service = Depends(get_crawler_execution_service),
    catalog_service = Depends(get_paper_catalog_service),
):
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}, catalog available only for completed jobs",
        )
    if topic_model:
        normalized_model = topic_model.lower()
        if normalized_model not in {"nmf", "lda"}:
            raise HTTPException(
                status_code=400,
                detail="topic_model must be either 'nmf' or 'lda'",
            )
        topic_model = normalized_model
    normalized_sort_dir = (sort_dir or 'desc').lower()
    if normalized_sort_dir not in {'asc', 'desc'}:
        raise HTTPException(
            status_code=400,
            detail="sort_dir must be 'asc' or 'desc'",
        )
    descending = normalized_sort_dir != 'asc'
    parser = StagingQueryParser()
    identifier_payload = parser.parse_identifier_filters(identifier_filters)
    custom_filters = parser.parse_column_filters(column_filters)

    try:
        return catalog_service.list_papers(
            job_id=job_id,
            page=page,
            page_size=page_size,
            query=query,
            venue=venue,
            doi=doi,
            year_from=year_from,
            year_to=year_to,
            topic=topic,
            topic_model=topic_model,
            topic_ids=topic_ids,
            doi_filter=doi_filter,
            seed_filter=seed_filter,
            retraction_filter=retraction_filter,
            seed_only=seed_only,
            retracted_only=retracted_only,
            mark_filters=marks,
            title_values=title_values,
            author_values=author_values,
            venue_values=venue_values,
            year_values=year_values,
            identifier_filters=identifier_payload,
            custom_filters=custom_filters,
            sort_by=sort_by,
            descending=descending,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Catalog not found for job {job_id}. Verify the crawl completed successfully.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/jobs/{job_id}/papers/column-options",
    response_model=ColumnOptionsPage,
    summary="Fetch paginated column-filter options for the catalog",
)
async def list_job_column_options(
    job_id: str = PathParam(..., description="Job ID"),
    column: str = Query(..., description="Column key to browse (title, authors, venue, year, identifier)"),
    page: int = Query(1, ge=1, description="Option page number"),
    page_size: int = Query(100, ge=1, le=500, description="Number of options per page"),
    option_query: Optional[str] = Query(None, description="Search text within column options"),
    query: Optional[str] = Query(None, description="Filter by title or paper identifier"),
    venue: Optional[str] = Query(None, description="Filter by venue name"),
    doi: Optional[str] = Query(None, description="Filter by DOI substring"),
    year_from: Optional[int] = Query(None, description="Lower bound for publication year"),
    year_to: Optional[int] = Query(None, description="Upper bound for publication year"),
    topic: Optional[int] = Query(
        None, description="Topic number to filter by (matches NMF and LDA unless topic_model is provided)"
    ),
    topic_model: Optional[str] = Query(
        None, description="Topic model to apply (nmf or lda)"
    ),
    topic_ids: Optional[List[int]] = Query(
        None,
        description="Repeatable topic filter (?topic_ids=1&topic_ids=2)",
    ),
    doi_filter: Optional[str] = Query(
        None, description="Filter by DOI presence (with, without, all)"
    ),
    seed_filter: Optional[str] = Query(
        None, description="Filter by seed status (with, without, all)"
    ),
    retraction_filter: Optional[str] = Query(
        None, description="Filter by retraction status (with, without, all)"
    ),
    seed_only: bool = Query(False, description="(Deprecated) Return only seed papers"),
    retracted_only: bool = Query(False, description="(Deprecated) Return only retracted papers"),
    marks: Optional[List[str]] = Query(
        None,
        alias="mark",
        description="Filter by annotation marks (repeatable)",
    ),
    title_values: Optional[List[str]] = Query(
        None, description="Exact title values selected from the column filter"
    ),
    author_values: Optional[List[str]] = Query(
        None, description="Author names selected from the column filter"
    ),
    venue_values: Optional[List[str]] = Query(
        None, description="Venue names selected from the column filter"
    ),
    year_values: Optional[List[int]] = Query(
        None, description="Publication years selected from the column filter"
    ),
    identifier_filters: Optional[List[str]] = Query(
        None,
        description="Identifier filters using the pattern 'field::value' (e.g. doi::10.1000/xyz)",
    ),
    column_filters: Optional[List[str]] = Query(
        None,
        description="Custom column filters using the format column::operator::value[::value_to]",
    ),
    crawler_service = Depends(get_crawler_execution_service),
    catalog_service = Depends(get_paper_catalog_service),
):
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}, catalog available only for completed jobs",
        )
    if topic_model:
        normalized_model = topic_model.lower()
        if normalized_model not in {"nmf", "lda"}:
            raise HTTPException(
                status_code=400,
                detail="topic_model must be either 'nmf' or 'lda'",
            )
        topic_model = normalized_model
    parser = StagingQueryParser()
    identifier_payload = parser.parse_identifier_filters(identifier_filters)
    custom_filters = parser.parse_column_filters(column_filters)

    try:
        return catalog_service.list_column_options(
            job_id=job_id,
            column=column,
            page=page,
            page_size=page_size,
            option_query=option_query,
            query=query,
            venue=venue,
            doi=doi,
            year_from=year_from,
            year_to=year_to,
            topic=topic,
            topic_model=topic_model,
            topic_ids=topic_ids,
            doi_filter=doi_filter,
            seed_filter=seed_filter,
            retraction_filter=retraction_filter,
            seed_only=seed_only,
            retracted_only=retracted_only,
            mark_filters=marks,
            title_values=title_values,
            author_values=author_values,
            venue_values=venue_values,
            year_values=year_values,
            identifier_filters=identifier_payload,
            custom_filters=custom_filters,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Catalog not found for job {job_id}. Verify the crawl completed successfully.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/jobs/{job_id}/papers/export",
    summary="Export the full catalog (with annotations) as an Excel file",
)
async def export_job_papers(
    job_id: str = PathParam(..., description="Job ID"),
    crawler_service = Depends(get_crawler_execution_service),
    catalog_service = Depends(get_paper_catalog_service),
):
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}, exports only available for completed jobs",
        )
    try:
        binary = catalog_service.export_catalog(job_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Catalog not found for job {job_id}. Verify the crawl completed successfully.",
        )

    filename = f"{job_id}_papers.xlsx"
    return StreamingResponse(
        io.BytesIO(binary),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.post(
    "/jobs/{job_id}/papers/{paper_id}/mark",
    response_model=PaperMarkResponse,
    summary="Annotate a paper within the catalog",
)
async def update_paper_mark(
    job_id: str = PathParam(..., description="Job ID"),
    paper_id: str = PathParam(..., description="Paper ID"),
    request: PaperMarkRequest = Body(...),
    crawler_service = Depends(get_crawler_execution_service),
    catalog_service = Depends(get_paper_catalog_service),
):
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}, annotations only available for completed jobs",
        )
    try:
        return catalog_service.update_mark(job_id, paper_id, request.mark)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Catalog not found for job {job_id}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/jobs/{job_id}/topics/{topic_id}/papers", response_model=TopicPapersResponse)
async def get_topic_papers(
    job_id: str = PathParam(..., description="Job ID"),
    topic_id: int = PathParam(..., description="Topic ID", ge=0),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Number of papers per page"),
    crawler_service = Depends(get_crawler_execution_service)
):
    """
    Paginated list of papers belonging to a specific topic.

    Each page includes:
    - topic metadata (id + label)
    - page information
    - papers enriched with provider metadata (title, authors, abstract, venue, etc.)
    """
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}, topic data only available for completed jobs"
        )
    
    topic_data = crawler_service.get_topic_papers(job_id, topic_id, page=page, page_size=page_size)
    if not topic_data:
        raise HTTPException(
            status_code=404,
            detail=f"Topic {topic_id} not found in job {job_id}"
        )
    
    return topic_data


@router.get(
    "/jobs/{job_id}/authors/{author_id}/papers",
    response_model=EntityPapersResponse,
)
async def get_author_papers(
    job_id: str = PathParam(..., description="Job ID"),
    author_id: str = PathParam(..., description="Author ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Number of papers per page"),
    crawler_service = Depends(get_crawler_execution_service),
):
    """
    Paginated list of papers belonging to a specific author retrieved from the API provider.
    """
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}, author data only available for completed jobs",
        )

    author_data = crawler_service.get_author_papers(
        job_id, author_id, page=page, page_size=page_size
    )
    if not author_data:
        raise HTTPException(
            status_code=404,
            detail=f"Author {author_id} not available for job {job_id}",
        )

    return author_data


@router.get(
    "/jobs/{job_id}/venues/{venue_id}/papers",
    response_model=EntityPapersResponse,
)
async def get_venue_papers(
    job_id: str = PathParam(..., description="Job ID"),
    venue_id: str = PathParam(..., description="Venue ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Number of papers per page"),
    crawler_service = Depends(get_crawler_execution_service),
):
    """
    Paginated list of papers published in a specific venue retrieved from the API provider.
    """
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}, venue data only available for completed jobs",
        )

    venue_data = crawler_service.get_venue_papers(
        job_id, venue_id, page=page, page_size=page_size
    )
    if not venue_data:
        raise HTTPException(
            status_code=404,
            detail=f"Venue {venue_id} not available for job {job_id}",
        )

    return venue_data
