"""In-memory storage stub. Stores .md strings keyed by unique_name."""

from __future__ import annotations

_store: dict[str, str] = {}


def read(name: str) -> str | None:
    return _store.get(name)


def write(name: str, content: str) -> None:
    _store[name] = content


def delete(name: str) -> bool:
    return _store.pop(name, None) is not None


def list_all() -> dict[str, str]:
    return dict(_store)
