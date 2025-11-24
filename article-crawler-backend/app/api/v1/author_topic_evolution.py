from fastapi import APIRouter, Depends, Body
from app.api.dependencies import get_author_topic_evolution_service
from app.schemas.author_topic_evolution import (
    SearchAuthorsRequest,
    SearchAuthorsResponse,
    StartAuthorEvolutionRequest,
    StartAuthorEvolutionResponse,
    AuthorCandidate,
    PeriodCount,
)


router = APIRouter()


@router.post("/search", response_model=SearchAuthorsResponse)
async def search_authors(
    request: SearchAuthorsRequest = Body(...),
    svc = Depends(get_author_topic_evolution_service)
):
    results = svc.search_authors(request.query, limit=request.limit, api_provider=request.api_provider)
    return SearchAuthorsResponse(
        query=request.query,
        total_results=len(results),
        authors=[AuthorCandidate(**r) for r in results]
    )


@router.post("/start", response_model=StartAuthorEvolutionResponse)
async def start_author_evolution(
    request: StartAuthorEvolutionRequest = Body(...),
    svc = Depends(get_author_topic_evolution_service)
):
    res = svc.run(
        author_id=request.author_id,
        model_type=request.model_type,
        num_topics=request.num_topics,
        time_period_years=request.time_period_years,
        api_provider=request.api_provider,
        max_papers=request.max_papers,
        save_library=request.save_library,
        library_path=request.library_path,
        output_path=request.output_path,
    )

    periods = [
        PeriodCount(period_label=p.label, paper_count=res.temporal_data.paper_counts_per_period[i])
        for i, p in enumerate(res.temporal_data.time_periods)
    ]

    return StartAuthorEvolutionResponse(
        author=AuthorCandidate(
            id=res.author.id,
            name=res.author.name,
            works_count=getattr(res.author, 'works_count', 0) or 0,
            cited_by_count=getattr(res.author, 'cited_by_count', 0) or 0,
            institutions=getattr(res.author, 'institutions', []) or [],
            orcid=getattr(res.author, 'orcid', None),
        ),
        model_type=res.model_type,
        num_topics=res.num_topics,
        time_period_years=res.time_period_years,
        total_papers=res.temporal_data.total_papers,
        periods=periods,
        topics_identified=list(res.temporal_data.topic_labels),
        emerging_topics=res.temporal_data.get_emerging_topics(),
        declining_topics=res.temporal_data.get_declining_topics(),
        is_temporary=res.is_temporary,
        visualization_path=str(res.visualization_path),
        library_path=str(res.library_path) if res.library_path else None,
        period_labels=[p.label for p in res.temporal_data.time_periods],
        topic_labels=list(res.temporal_data.topic_labels),
        topic_proportions=list(res.temporal_data.topic_distributions),
    )