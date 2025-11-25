from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.core.container import Container
from app.api.v1 import router as api_v1_router
from app.core.exceptions import ArticleCrawlerException, to_http_exception


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)

logger = logging.getLogger("ArticleCrawlerAPI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    
    logger.info("Starting ArticleCrawler API...")
    logger.info(f"ArticleCrawler path: {settings.ARTICLECRAWLER_PATH}")
    
    container = Container()
    config_payload = settings.model_dump()
    if "STAGED_FILES_DIR" not in config_payload:
        config_payload["STAGED_FILES_DIR"] = settings.STAGED_FILES_DIR
    container.config.from_dict(config_payload)
    
    # Wire dependencies
    container.wire(modules=[
        "app.api.v1.router",
        "app.api.v1.seeds",
        "app.api.v1.seed_sessions",
        "app.api.v1.pdf_seeds",
        "app.api.v1.zotero_seeds",
        "app.api.v1.keywords",
        "app.api.v1.configuration",
        "app.api.v1.crawler_execution",
        "app.api.v1.library",
        "app.api.v1.author_topic_evolution",
        "app.api.dependencies",
    ])
    
    app.state.container = container

    # Cleanup stale staged file sessions on startup
    staged_file_service = container.source_file_service()
    removed_count = staged_file_service.cleanup_expired_sessions(settings.STAGED_FILES_TTL_HOURS)
    if removed_count:
        logger.info("Startup cleanup removed %d expired staged file session(s)", removed_count)
    
    logger.info(f"API started successfully on {settings.API_V1_PREFIX}")
    
    try:
        yield
    finally:
        executor = container.job_executor()
        executor.shutdown(wait=False)
    
    logger.info("Shutting down ArticleCrawler API...")
    container.unwire()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_v1_router.router,
    prefix=settings.API_V1_PREFIX
)


@app.exception_handler(ArticleCrawlerException)
async def handle_domain_exceptions(request: Request, exc: ArticleCrawlerException):
    http_exc = to_http_exception(exc)
    return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})


@app.exception_handler(Exception)
async def handle_generic_exceptions(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ArticleCrawler API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
