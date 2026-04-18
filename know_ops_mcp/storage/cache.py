"""Cache decorator for ExternalStorage backends.

Wraps an `ExternalStorage` and serves reads and listings from a local disk
cache. Cache is populated on first read/list; subsequent calls are served
entirely from disk with zero network requests.

Writes are write-through (backend + cache updated together). TTL is infinite.
Use `refresh()` to evict cache entries; the next read/list re-fetches from
the backend.
"""

from __future__ import annotations

import os
from pathlib import Path

from know_ops_mcp.storage import disk
from know_ops_mcp.storage.backends.external import ExternalStorage
from know_ops_mcp.storage.base import BaseStorage

_POPULATED_MARKER = ".list-populated"


def default_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    return Path(base).expanduser() / "know-ops-mcp"


class CachedStorage(BaseStorage):
    def __init__(self, backend: ExternalStorage, cache_dir: str | Path) -> None:
        self._backend = backend
        self._cache_root = Path(cache_dir).expanduser().resolve()
        disk.ensure(self._cache_root)

    def _marker(self) -> Path:
        return self._cache_root / _POPULATED_MARKER

    def read(self, name: str) -> str | None:
        cached = disk.read(self._cache_root, name)
        if cached is not None:
            return cached
        fresh = self._backend.read(name)
        if fresh is not None:
            disk.write(self._cache_root, name, fresh)
        return fresh

    def write(self, name: str, content: str) -> None:
        self._backend.write(name, content)
        disk.write(self._cache_root, name, content)

    def delete(self, name: str) -> bool:
        result = self._backend.delete(name)
        disk.delete(self._cache_root, name)
        return result

    def list_all(self) -> dict[str, str]:
        if self._marker().exists():
            return disk.list_all(self._cache_root)
        result: dict[str, str] = {}
        for name in self._backend.list_versions():
            text = self.read(name)
            if text is not None:
                result[name] = text
        self._marker().touch()
        return result

    def refresh(self, name: str | None = None) -> None:
        if name is None:
            disk.clear(self._cache_root)
            self._marker().unlink(missing_ok=True)
        else:
            disk.delete(self._cache_root, name)
