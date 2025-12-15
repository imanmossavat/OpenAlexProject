from fastapi import APIRouter
from . import (
    seeds,
    seed_sessions,
    pdf_seeds,
    zotero_seeds,
    staging,
    keywords,
    configuration,
    crawler_execution,
    crawler_rerun,
    library,
    author_topic_evolution,
    settings,
    papers,
)

router = APIRouter()

router.include_router(
    seeds.router,
    prefix="/seeds",
    tags=["Seeds"]
)

router.include_router(
    seed_sessions.router,
    prefix="/seeds/session",
    tags=["Seed Sessions"]
)

router.include_router(
    pdf_seeds.router,
    prefix="/seeds/session",
    tags=["PDF Seeds"]
)

router.include_router(
    staging.router,
    tags=["Staging"]
)

router.include_router(
    zotero_seeds.router
)

router.include_router(
    keywords.router, 
    prefix="/seeds/session", 
    tags=["Keywords"]
)

router.include_router(
    configuration.router,
    prefix="/seeds/session",
    tags=["Configuration"]
)

router.include_router(
    crawler_execution.router,
    prefix="/crawler",
    tags=["Crawler Execution"]
)

router.include_router(
    crawler_rerun.router,
    prefix="/crawler/reruns",
    tags=["Crawler Reruns"]
)

router.include_router(
    library.router,
    prefix="/library",
    tags=["Library"]
)

router.include_router(
    author_topic_evolution.router,
    prefix="/author-topic-evolution",
    tags=["Author Topic Evolution"]
)

router.include_router(
    settings.router
)

router.include_router(
    papers.router,
    prefix="/papers",
    tags=["Papers"]
)



@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "ArticleCrawler API is running"}
