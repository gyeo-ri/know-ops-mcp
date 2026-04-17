"""Local directory storage. One `.md` file per knowledge_key under a base directory."""

from __future__ import annotations

import os
from pathlib import Path

from know_ops_mcp.storage import disk
from know_ops_mcp.storage.backends.internal import InternalStorage


def default_data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or "~/.local/share"
    return Path(base).expanduser() / "know-ops-mcp"


class LocalDirectoryStorage(InternalStorage):
    def __init__(self, path: str | Path) -> None:
        self._root = Path(path).expanduser().resolve()
        disk.ensure(self._root)

    def read(self, name: str) -> str | None:
        return disk.read(self._root, name)

    def write(self, name: str, content: str) -> None:
        disk.write(self._root, name, content)

    def delete(self, name: str) -> bool:
        return disk.delete(self._root, name)

    def list_all(self) -> dict[str, str]:
        return disk.list_all(self._root)
