"""know-ops-mcp CLI entrypoint. Subcommands: serve (default), setup."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="know-ops-mcp",
    help="Shared knowledge MCP server.",
    no_args_is_help=False,
    add_completion=False,
)


@app.command()
def serve() -> None:
    """Run the MCP server (stdio). Invoked automatically by your MCP client."""
    from know_ops_mcp.server import main

    main()


@app.command()
def setup() -> None:
    """Interactive setup. Re-run anytime to view current config or change it."""
    from know_ops_mcp.setup.wizard import run

    run()


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        serve()
