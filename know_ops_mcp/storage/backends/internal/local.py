"""Local directory storage. One `.md` file per unique_name under a base directory."""

from __future__ import annotations

from pathlib import Path

from know_ops_mcp.storage import disk
from know_ops_mcp.storage.backends.internal import InternalStorage


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
