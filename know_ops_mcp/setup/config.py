"""User-facing configuration. Persisted as TOML under XDG config dir."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel

from know_ops_mcp.know_ops.storage.base import BaseStorage
from know_ops_mcp.know_ops.storage.backends.internal.local import LocalDirectoryStorage


class StorageConfig(BaseModel):
    path: str


class Config(BaseModel):
    storage: StorageConfig

    @staticmethod
    def location() -> Path:
        base = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
        return Path(base).expanduser() / "know-ops-mcp" / "config.toml"

    @classmethod
    def load(cls) -> "Config | None":
        p = cls.location()
        if not p.is_file():
            return None
        with p.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)

    def save(self) -> None:
        p = self.location()
        p.parent.mkdir(parents=True, exist_ok=True)
        escaped = self.storage.path.replace("\\", "\\\\").replace('"', '\\"')
        p.write_text(f'[storage]\npath = "{escaped}"\n', encoding="utf-8")

    def to_storage_backend(self) -> BaseStorage:
        return LocalDirectoryStorage(self.storage.path)
