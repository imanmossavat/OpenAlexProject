from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from threading import RLock
from typing import Dict, List, Optional

from ArticleCrawler.crawler import Crawler


class CrawlerJobStore(ABC):
    """Storage abstraction for crawler jobs and their results."""

    @abstractmethod
    def create_job(self, job_id: str, data: Dict) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def update_job(self, job_id: str, **updates) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def list_jobs(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def delete_job(self, job_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def store_crawler(self, job_id: str, crawler: Crawler) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_crawler(self, job_id: str) -> Optional[Crawler]:
        raise NotImplementedError


class InMemoryCrawlerJobStore(CrawlerJobStore):
    """Thread-safe in-memory implementation of crawler job storage."""

    def __init__(self):
        self._jobs: Dict[str, Dict] = {}
        self._crawlers: Dict[str, Crawler] = {}
        self._lock = RLock()

    def create_job(self, job_id: str, data: Dict) -> Dict:
        with self._lock:
            self._jobs[job_id] = deepcopy(data)
        return data

    def update_job(self, job_id: str, **updates) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(updates)

    def get_job(self, job_id: str) -> Optional[Dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            return deepcopy(job) if job else None

    def list_jobs(self) -> List[Dict]:
        with self._lock:
            return [deepcopy(job) for job in self._jobs.values()]

    def delete_job(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)
            self._crawlers.pop(job_id, None)

    def store_crawler(self, job_id: str, crawler: Crawler) -> None:
        with self._lock:
            self._crawlers[job_id] = crawler

    def get_crawler(self, job_id: str) -> Optional[Crawler]:
        with self._lock:
            return self._crawlers.get(job_id)

