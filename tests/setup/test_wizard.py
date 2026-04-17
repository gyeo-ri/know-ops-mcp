import json

import pytest

from know_ops_mcp.setup import wizard
from know_ops_mcp.setup.config import GitHubStorageConfig, LocalStorageConfig


class _FakeDist:
    def __init__(self, payload: str | None) -> None:
        self._payload = payload

    def read_text(self, name: str) -> str | None:
        assert name == "direct_url.json"
        return self._payload


def _patch_distribution(monkeypatch, payload: str | None) -> None:
    monkeypatch.setattr(
        wizard.metadata,
        "distribution",
        lambda _name: _FakeDist(payload),
    )


def _patch_distribution_missing(monkeypatch) -> None:
    def _raise(_name):
        raise wizard.metadata.PackageNotFoundError(_name)

    monkeypatch.setattr(wizard.metadata, "distribution", _raise)


class TestNonempty:
    def test_accepts_text(self):
        assert wizard._nonempty("hello") is True

    def test_rejects_blank(self):
        assert wizard._nonempty("   ") == "Cannot be empty."

    def test_rejects_empty(self):
        assert wizard._nonempty("") == "Cannot be empty."


class TestInstallSource:
    def test_package_not_found_returns_none(self, monkeypatch):
        _patch_distribution_missing(monkeypatch)
        assert wizard._install_source() is None

    def test_empty_payload_returns_none(self, monkeypatch):
        _patch_distribution(monkeypatch, "")
        assert wizard._install_source() is None

    def test_vcs_info_with_commit_id(self, monkeypatch):
        payload = json.dumps({
            "url": "https://github.com/owner/repo",
            "vcs_info": {"vcs": "git", "commit_id": "abc123"},
        })
        _patch_distribution(monkeypatch, payload)
        assert wizard._install_source() == "git+https://github.com/owner/repo@abc123"

    def test_vcs_info_falls_back_to_requested_revision(self, monkeypatch):
        payload = json.dumps({
            "url": "https://github.com/owner/repo",
            "vcs_info": {"vcs": "git", "requested_revision": "main"},
        })
        _patch_distribution(monkeypatch, payload)
        assert wizard._install_source() == "git+https://github.com/owner/repo@main"

    def test_vcs_info_without_ref(self, monkeypatch):
        payload = json.dumps({
            "url": "https://github.com/owner/repo",
            "vcs_info": {"vcs": "git"},
        })
        _patch_distribution(monkeypatch, payload)
        assert wizard._install_source() == "git+https://github.com/owner/repo"

    def test_dir_info_returns_local_path(self, monkeypatch):
        payload = json.dumps({
            "url": "file:///abs/path/to/repo",
            "dir_info": {"editable": True},
        })
        _patch_distribution(monkeypatch, payload)
        assert wizard._install_source() == "/abs/path/to/repo"

    def test_neither_vcs_nor_dir_returns_none(self, monkeypatch):
        payload = json.dumps({"url": "https://example.com"})
        _patch_distribution(monkeypatch, payload)
        assert wizard._install_source() is None


class TestUvxArgs:
    def test_no_source_returns_just_server_name(self, monkeypatch):
        _patch_distribution_missing(monkeypatch)
        assert wizard._uvx_args() == [wizard.SERVER_NAME]

    def test_with_source_includes_from_flag(self, monkeypatch):
        payload = json.dumps({
            "url": "file:///abs/repo",
            "dir_info": {},
        })
        _patch_distribution(monkeypatch, payload)
        assert wizard._uvx_args() == ["--from", "/abs/repo", wizard.SERVER_NAME]


class TestPrintSnippet:
    def test_warns_when_uvx_missing(self, monkeypatch, capsys):
        _patch_distribution_missing(monkeypatch)
        monkeypatch.setattr(wizard.shutil, "which", lambda _name: None)
        wizard._print_snippet()
        out = capsys.readouterr().out
        assert '"command": "uvx"' in out
        assert "[warning]" in out
        assert "uvx" in out
        assert wizard.UV_INSTALL_URL in out

    def test_no_warning_when_uvx_present(self, monkeypatch, capsys):
        _patch_distribution_missing(monkeypatch)
        monkeypatch.setattr(wizard.shutil, "which", lambda _name: "/usr/bin/uvx")
        wizard._print_snippet()
        out = capsys.readouterr().out
        assert '"command": "uvx"' in out
        assert "[warning]" not in out


class TestPrintExisting:
    def test_local_backend_format(self, capsys):
        wizard._print_existing(LocalStorageConfig(path="/tmp/data"))
        out = capsys.readouterr().out
        assert "type = local" in out
        assert "/tmp/data" in out

    def test_github_backend_with_token(self, capsys):
        wizard._print_existing(
            GitHubStorageConfig(
                repo_url="https://github.com/o/r",
                token="abc",
                branch="dev",
                subdirectory="kb",
            )
        )
        out = capsys.readouterr().out
        assert "type = github" in out
        assert "https://github.com/o/r" in out
        assert "branch       = dev" in out
        assert "subdirectory = kb" in out
        assert "token        = set" in out

    def test_github_backend_without_token_mentions_env_var(self, capsys):
        wizard._print_existing(
            GitHubStorageConfig(repo_url="https://github.com/o/r", token="")
        )
        out = capsys.readouterr().out
        assert "subdirectory = (root)" in out
        assert "unset" in out
        assert "KNOW_OPS_MCP_GITHUB_TOKEN" in out
