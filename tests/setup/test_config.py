import os
import stat

import pytest

from know_ops_mcp.setup.config import (
    TOKEN_ENV_VAR,
    Config,
    GitHubStorageConfig,
    LocalStorageConfig,
)


@pytest.fixture
def isolated_xdg_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv(TOKEN_ENV_VAR, raising=False)
    return tmp_path


def test_load_returns_none_when_file_missing(isolated_xdg_config):
    assert Config.load() is None


def test_save_then_load_round_trip_local(isolated_xdg_config):
    cfg = Config(storage=LocalStorageConfig(path="/tmp/example"))
    cfg.save()

    loaded = Config.load()
    assert isinstance(loaded.storage, LocalStorageConfig)
    assert loaded.storage.path == "/tmp/example"


def test_save_then_load_round_trip_github(isolated_xdg_config):
    cfg = Config(
        storage=GitHubStorageConfig(
            repo_url="https://github.com/o/r",
            branch="dev",
            subdirectory="notes",
            token="secret",
        )
    )
    cfg.save()

    loaded = Config.load()
    assert isinstance(loaded.storage, GitHubStorageConfig)
    assert loaded.storage.repo_url == "https://github.com/o/r"
    assert loaded.storage.branch == "dev"
    assert loaded.storage.subdirectory == "notes"
    assert loaded.storage.token == "secret"


def test_save_sets_owner_only_permission(isolated_xdg_config):
    cfg = Config(storage=LocalStorageConfig(path="/tmp/x"))
    cfg.save()

    mode = stat.S_IMODE(os.stat(Config.location()).st_mode)
    assert mode == 0o600


def test_resolve_token_prefers_env_over_config(isolated_xdg_config, monkeypatch):
    monkeypatch.setenv(TOKEN_ENV_VAR, "from-env")
    cfg = GitHubStorageConfig(repo_url="https://github.com/o/r", token="from-config")
    assert cfg.resolve_token() == "from-env"


def test_resolve_token_falls_back_to_config(isolated_xdg_config):
    cfg = GitHubStorageConfig(repo_url="https://github.com/o/r", token="from-config")
    assert cfg.resolve_token() == "from-config"


def test_resolve_token_raises_when_neither_present(isolated_xdg_config):
    cfg = GitHubStorageConfig(repo_url="https://github.com/o/r")
    with pytest.raises(RuntimeError, match="requires a token"):
        cfg.resolve_token()


def test_resolve_token_treats_blank_env_as_unset(isolated_xdg_config, monkeypatch):
    monkeypatch.setenv(TOKEN_ENV_VAR, "   ")
    cfg = GitHubStorageConfig(repo_url="https://github.com/o/r", token="from-config")
    assert cfg.resolve_token() == "from-config"
