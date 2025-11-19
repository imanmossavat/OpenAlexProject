from fastapi import APIRouter, Depends, HTTPException, Path as PathParam
from typing import List
import logging

from app.api.dependencies import (
    get_crawler_execution_service, 
    get_seed_session_service,
    get_keyword_service,
    get_configuration_service,
    get_library_service,
)
from app.schemas.crawler_execution import (
    StartCrawlerRequest, StartCrawlerResponse, CrawlerStatus,
    CrawlerResults, TopicPapersResponse
)

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

    session_data = {
        "session_id": session.session_id,
        "use_case": session.use_case,
        "seeds": [seed.model_dump() for seed in session.seeds],
        "keywords": keyword_service.get_keywords(session_id),
        "configuration": config_service.get_final_config_dict(session_id),
        "created_at": session.created_at,
        "updated_at": session.updated_at
    }

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


@router.get("/jobs/{job_id}/topics/{topic_id}/papers", response_model=TopicPapersResponse)
async def get_topic_papers(
    job_id: str = PathParam(..., description="Job ID"),
    topic_id: int = PathParam(..., description="Topic ID", ge=0),
    crawler_service = Depends(get_crawler_execution_service)
):
    """
    Get all papers belonging to a specific topic.
    
    Returns:
    - topic_id: Topic identifier
    - topic_label: Human-readable topic label
    - papers: List of all papers in this topic with full metadata
    - total_count: Total number of papers
    
    Papers are returned with:
    - Full metadata (title, authors, year, venue)
    - Centrality scores
    - Citation counts
    - URLs
    - Seed/retracted status
    """
    status = crawler_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is {status['status']}, topic data only available for completed jobs"
        )
    
    topic_data = crawler_service.get_topic_papers(job_id, topic_id)
    if not topic_data:
        raise HTTPException(
            status_code=404,
            detail=f"Topic {topic_id} not found in job {job_id}"
        )
    
    return topic_data