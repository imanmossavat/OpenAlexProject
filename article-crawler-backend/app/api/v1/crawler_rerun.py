from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

from app.api.dependencies import get_crawler_rerun_service
from app.schemas.crawler_rerun import (
    ExperimentListResponse,
    ExperimentSummary,
    LoadExperimentByPathRequest,
    LoadExperimentRequest,
    LoadExperimentResponse,
)
from app.services.crawler_rerun_service import CrawlerRerunService

router = APIRouter()


@router.get("/experiments", response_model=ExperimentListResponse)
async def list_experiments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    query: Optional[str] = Query(None, description="Search string for name or job ID"),
    service: CrawlerRerunService = Depends(get_crawler_rerun_service),
):
    total, experiments, root_path = service.list_experiments(page=page, page_size=page_size, query=query)
    return ExperimentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        experiments=experiments,
        root_path=root_path,
    )


@router.post("/experiments/{job_id}/load", response_model=LoadExperimentResponse)
async def load_experiment_into_session(
    job_id: str = Path(..., description="Job ID of the saved experiment"),
    request: LoadExperimentRequest = Body(...),
    service: CrawlerRerunService = Depends(get_crawler_rerun_service),
):
    try:
        summary = service.load_into_session(job_id, request.session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Experiment {job_id} not found")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return LoadExperimentResponse(
        session_id=request.session_id,
        job_id=job_id,
        experiment=summary,
    )


@router.post("/experiments/load-by-path", response_model=LoadExperimentResponse)
async def load_experiment_by_path(
    request: LoadExperimentByPathRequest = Body(...),
    service: CrawlerRerunService = Depends(get_crawler_rerun_service),
):
    try:
        summary = service.load_from_path(request.session_id, request.experiment_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Experiment not found at {request.experiment_path}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return LoadExperimentResponse(
        session_id=request.session_id,
        job_id=summary.job_id,
        experiment=summary,
    )
