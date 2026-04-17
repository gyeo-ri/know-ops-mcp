"""Storage service: facade over a swappable BaseStorage backend."""

from __future__ import annotations

from know_ops_mcp.storage.backends.external import ExternalStorage
from know_ops_mcp.storage.backends.external.github import GitHubStorage
from know_ops_mcp.storage.backends.internal.local import (
    LocalDirectoryStorage,
    default_data_dir,
)
from know_ops_mcp.storage.backends.internal.memory import MemoryStorage
from know_ops_mcp.storage.base import BaseStorage
from know_ops_mcp.storage.cache import CachedStorage, default_cache_dir


class StorageService:
    def __init__(self, backend: BaseStorage) -> None:
        self._backend = backend

    def configure(self, backend: BaseStorage) -> None:
        self._backend = backend

    def read(self, name: str) -> str | None:
        return self._backend.read(name)

    def write(self, name: str, content: str) -> None:
        self._backend.write(name, content)

    def delete(self, name: str) -> bool:
        return self._backend.delete(name)

    def list_all(self) -> dict[str, str]:
        return self._backend.list_all()

    def refresh(self, name: str | None = None) -> None:
        fn = getattr(self._backend, "refresh", None)
        if fn is None:
            return
        fn(name)


storage = StorageService(MemoryStorage())


__all__ = [
    "BaseStorage",
    "CachedStorage",
    "ExternalStorage",
    "GitHubStorage",
    "LocalDirectoryStorage",
    "MemoryStorage",
    "StorageService",
    "default_cache_dir",
    "default_data_dir",
    "storage",
]
