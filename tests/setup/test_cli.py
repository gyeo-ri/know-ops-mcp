import pytest
from typer.testing import CliRunner

from know_ops_mcp.setup import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def patched(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        "know_ops_mcp.server.main", lambda: calls.append("serve")
    )
    monkeypatch.setattr(
        "know_ops_mcp.setup.wizard.run", lambda: calls.append("setup")
    )
    return calls


def test_serve_subcommand_invokes_server_main(runner, patched):
    result = runner.invoke(cli.app, ["serve"])
    assert result.exit_code == 0
    assert patched == ["serve"]


def test_setup_subcommand_invokes_wizard_run(runner, patched):
    result = runner.invoke(cli.app, ["setup"])
    assert result.exit_code == 0
    assert patched == ["setup"]


def test_default_no_args_invokes_serve(runner, patched):
    result = runner.invoke(cli.app, [])
    assert result.exit_code == 0
    assert patched == ["serve"]


def test_help_includes_uvx_epilog(runner):
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "uvx know-ops-mcp" in result.stdout
    assert "https://docs.astral.sh/uv/getting-started/installation/" in result.stdout
