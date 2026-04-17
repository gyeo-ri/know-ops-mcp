"""Disk R/W helpers shared across the storage package.

Convention: one `<name>.md` file per entry under a given root directory.
Used by `LocalDirectoryStorage` (backend) and `CachedStorage` (cache layer).

Writes are atomic via temp file + rename: the target file either reflects
the previous version or the new one, never a partially-written body. The
temp file lives next to the target (same filesystem) so the rename is
truly atomic on POSIX; `Path.replace` covers Windows by overwriting an
existing target.
"""

from __future__ import annotations

from pathlib import Path


def ensure(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)


def _file(root: Path, name: str) -> Path:
    target = root / f"{name}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def read(root: Path, name: str) -> str | None:
    f = _file(root, name)
    if not f.is_file():
        return None
    return f.read_text(encoding="utf-8")


def write(root: Path, name: str, content: str) -> None:
    target = _file(root, name)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)


def delete(root: Path, name: str) -> bool:
    f = _file(root, name)
    if not f.is_file():
        return False
    f.unlink()
    _prune_empty_parents(f.parent, root)
    return True


def list_all(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).with_suffix("").as_posix(): p.read_text(encoding="utf-8")
        for p in root.rglob("*.md")
    }


def clear(root: Path) -> None:
    for p in root.rglob("*.md"):
        p.unlink()
    _prune_empty_dirs(root)


def _prune_empty_parents(directory: Path, root: Path) -> None:
    while directory != root:
        try:
            directory.rmdir()
        except OSError:
            break
        directory = directory.parent


def _prune_empty_dirs(root: Path) -> None:
    for d in sorted(root.rglob("*"), reverse=True):
        if d.is_dir():
            try:
                d.rmdir()
            except OSError:
                pass
