from pydantic_settings import BaseSettings
from typing import List

from app.core.bootstrap import ensure_articlecrawler_path

ARTICLECRAWLER_PATH = ensure_articlecrawler_path()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    ARTICLECRAWLER_PATH: str = ARTICLECRAWLER_PATH
    
    PROJECT_NAME: str = "ArticleCrawler API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    REQUEST_TIMEOUT_SECONDS: int = 1800
    STAGED_FILES_DIR: str = "uploaded_dumps"
    STAGED_FILES_TTL_HOURS: int = 48
    RETRACTION_CACHE_DIR: str = "retraction_cache"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()
