"""Local directory storage. One `.md` file per unique_name under a base directory."""

from __future__ import annotations

from pathlib import Path

from know_ops_mcp.know_ops.storage.backends.internal import InternalStorage


class LocalDirectoryStorage(InternalStorage):
    def __init__(self, path: str | Path) -> None:
        self._root = Path(path).expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _file(self, name: str) -> Path:
        return self._root / f"{name}.md"

    def read(self, name: str) -> str | None:
        f = self._file(name)
        if not f.is_file():
            return None
        return f.read_text(encoding="utf-8")

    def write(self, name: str, content: str) -> None:
        self._file(name).write_text(content, encoding="utf-8")

    def delete(self, name: str) -> bool:
        f = self._file(name)
        if not f.is_file():
            return False
        f.unlink()
        return True

    def list_all(self) -> dict[str, str]:
        return {p.stem: p.read_text(encoding="utf-8") for p in self._root.glob("*.md")}
