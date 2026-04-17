"""In-memory storage implementation. Stores .md strings keyed by unique_name."""

from __future__ import annotations

from know_ops_mcp.storage.backends.internal import InternalStorage


class MemoryStorage(InternalStorage):
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def read(self, name: str) -> str | None:
        return self._store.get(name)

    def write(self, name: str, content: str) -> None:
        self._store[name] = content

    def delete(self, name: str) -> bool:
        return self._store.pop(name, None) is not None

    def list_all(self) -> dict[str, str]:
        return dict(self._store)
