"""Interactive setup wizard. Picks a storage path and saves config.

Re-running the wizard with an existing config doubles as a "show me my
current config + the snippet" command (answer 'no' to the modify prompt).
"""

from __future__ import annotations

import json

import questionary

from know_ops_mcp.storage.backends.internal.local import LocalDirectoryStorage
from know_ops_mcp.setup.config import Config, StorageConfig

DEFAULT_PATH = "~/Documents/know-ops-mcp"
SERVER_NAME = "know-ops-mcp"


def run() -> None:
    print("know-ops-mcp setup\n")

    existing = Config.load()
    if existing is not None:
        print(f"Existing config: {Config.location()}")
        print(f"  storage path = {existing.storage.path}\n")
        if not questionary.confirm("Modify existing config?", default=True).ask():
            _print_snippet()
            return

    default = existing.storage.path if existing else DEFAULT_PATH
    path_str = questionary.text(
        "Storage directory:",
        default=default,
        validate=_validate_path,
    ).ask()
    if path_str is None:
        print("Setup cancelled.")
        return

    try:
        LocalDirectoryStorage(path_str)
    except OSError as e:
        print(f"Error: cannot prepare directory '{path_str}': {e}")
        return

    Config(storage=StorageConfig(path=path_str)).save()
    print(f"\nConfig saved: {Config.location()}")
    _print_snippet()


def _print_snippet() -> None:
    snippet = json.dumps(
        {"mcpServers": {SERVER_NAME: {"command": SERVER_NAME}}},
        indent=2,
    )
    print("\nRegister this MCP server with your client:\n")
    for line in snippet.splitlines():
        print(f"  {line}")
    print(
        "\nConsult your MCP client's documentation for where to put this snippet,\n"
        "then restart the client."
    )


def _validate_path(value: str) -> bool | str:
    return True if value.strip() else "Path cannot be empty."
