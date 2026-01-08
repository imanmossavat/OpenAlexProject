from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any


class BackgroundJobExecutor:
    """Thin wrapper around ThreadPoolExecutor for crawler jobs."""

    def __init__(self, max_workers: int = 2):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="crawler-job")

    def submit(self, fn: Callable[..., Any], *args, **kwargs) -> Future:
        return self._executor.submit(fn, *args, **kwargs)

    def shutdown(self, wait: bool = False):
        self._executor.shutdown(wait=wait)

