from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import shutil
import tempfile

from fastapi import UploadFile


class FileStorageAdapter(ABC):
    """Abstraction over filesystem interactions for uploads."""

    @abstractmethod
    def create_temp_dir(self, prefix: str) -> Path:
        raise NotImplementedError

    @abstractmethod
    def save_upload(self, directory: Path, filename: str, uploaded_file: UploadFile) -> Path:
        raise NotImplementedError

    @abstractmethod
    def remove_dir(self, directory: Path) -> None:
        raise NotImplementedError


class LocalTempFileStorage(FileStorageAdapter):
    """Local filesystem implementation for temporary file storage."""

    def create_temp_dir(self, prefix: str) -> Path:
        return Path(tempfile.mkdtemp(prefix=prefix))

    def save_upload(self, directory: Path, filename: str, uploaded_file: UploadFile) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / filename
        with open(destination, "wb") as dest:
            shutil.copyfileobj(uploaded_file.file, dest)
        return destination

    def remove_dir(self, directory: Path) -> None:
        if directory.exists():
            shutil.rmtree(directory)

