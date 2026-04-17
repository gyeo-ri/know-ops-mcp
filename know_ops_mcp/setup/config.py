"""User-facing configuration. Persisted as TOML under XDG config dir.

Discriminated union: `local` (filesystem path) or `github` (repo + token).
The token may also be supplied via `KNOW_OPS_MCP_GITHUB_TOKEN` env var as
an escape hatch for CI/scripted environments.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Annotated, Literal, Union

import tomli_w
from pydantic import BaseModel, Field

from know_ops_mcp.storage import (
    BaseStorage,
    CachedStorage,
    GitHubStorage,
    LocalDirectoryStorage,
    default_cache_dir,
)

TOKEN_ENV_VAR = "KNOW_OPS_MCP_GITHUB_TOKEN"


class LocalStorageConfig(BaseModel):
    type: Literal["local"] = "local"
    path: str


class GitHubStorageConfig(BaseModel):
    type: Literal["github"] = "github"
    repo_url: str
    branch: str = "main"
    subdirectory: str = ""
    token: str = ""

    def resolve_token(self) -> str:
        env = os.environ.get(TOKEN_ENV_VAR, "").strip()
        if env:
            return env
        if not self.token:
            raise RuntimeError(
                f"GitHub backend requires a token. Set storage.token in "
                f"{Config.location()} or the {TOKEN_ENV_VAR} env var."
            )
        return self.token


StorageConfig = Annotated[
    Union[LocalStorageConfig, GitHubStorageConfig],
    Field(discriminator="type"),
]


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
        p.write_bytes(tomli_w.dumps(self.model_dump()).encode("utf-8"))
        p.chmod(0o600)

    def to_storage_backend(self) -> BaseStorage:
        s = self.storage
        if isinstance(s, LocalStorageConfig):
            return LocalDirectoryStorage(s.path)
        if isinstance(s, GitHubStorageConfig):
            return CachedStorage(
                GitHubStorage(
                    s.repo_url,
                    token=s.resolve_token(),
                    branch=s.branch,
                    subdirectory=s.subdirectory,
                ),
                cache_dir=default_cache_dir(),
            )
        raise RuntimeError(f"Unknown storage type: {s!r}")
