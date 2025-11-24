
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def ensure_articlecrawler_path() -> str:
    """Ensure the ArticleCrawler source path is present on sys.path."""
    articlecrawler_path = os.getenv("ARTICLECRAWLER_PATH")
    if not articlecrawler_path:
        raise RuntimeError("Set ARTICLECRAWLER_PATH in .env to the project root")

    resolved_path = str(Path(articlecrawler_path).expanduser().resolve())
    if resolved_path not in sys.path:
        sys.path.insert(0, resolved_path)
    return resolved_path

