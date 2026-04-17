"""Interactive setup wizard. Picks a backend and saves config.

Re-running the wizard with an existing config doubles as a "show me my
current config + the snippet" command (answer 'no' to the modify prompt).

For GitHub, only repo URL + token are prompted. Branch and subdirectory
default to `main` / root; edit `config.toml` directly to change them.
"""

from __future__ import annotations

import json

import questionary

from know_ops_mcp.setup.config import (
    TOKEN_ENV_VAR,
    Config,
    GitHubStorageConfig,
    LocalStorageConfig,
    StorageConfig,
)
from know_ops_mcp.storage.backends.internal.local import LocalDirectoryStorage

DEFAULT_LOCAL_PATH = "~/Documents/know-ops-mcp"
SERVER_NAME = "know-ops-mcp"


def run() -> None:
    print(f"{SERVER_NAME} setup\n")

    existing = Config.load()
    if existing is not None:
        print(f"Existing config: {Config.location()}")
        _print_existing(existing.storage)
        if not questionary.confirm("Modify existing config?", default=True).ask():
            _print_snippet()
            return

    default_backend = existing.storage.type if existing else "local"
    backend_type = questionary.select(
        "Storage backend:",
        choices=["local", "github"],
        default=default_backend,
    ).ask()
    if backend_type is None:
        print("Setup cancelled.")
        return

    storage = (
        _prompt_local(existing) if backend_type == "local" else _prompt_github(existing)
    )
    if storage is None:
        return

    Config(storage=storage).save()
    print(f"\nConfig saved: {Config.location()}")
    _print_snippet()


def _prompt_local(existing: Config | None) -> LocalStorageConfig | None:
    default = (
        existing.storage.path
        if existing and isinstance(existing.storage, LocalStorageConfig)
        else DEFAULT_LOCAL_PATH
    )
    path = questionary.text(
        "Storage directory:",
        default=default,
        validate=_nonempty,
    ).ask()
    if path is None:
        print("Setup cancelled.")
        return None
    try:
        LocalDirectoryStorage(path)
    except OSError as e:
        print(f"Error: cannot prepare directory '{path}': {e}")
        return None
    return LocalStorageConfig(path=path)


def _prompt_github(existing: Config | None) -> GitHubStorageConfig | None:
    prev = (
        existing.storage
        if existing and isinstance(existing.storage, GitHubStorageConfig)
        else None
    )
    repo_url = questionary.text(
        "GitHub repo URL (https://github.com/owner/repo):",
        default=prev.repo_url if prev else "",
        validate=_nonempty,
    ).ask()
    if repo_url is None:
        print("Setup cancelled.")
        return None
    token = questionary.password(
        f"GitHub token (leave blank to use ${TOKEN_ENV_VAR} instead):",
    ).ask()
    if token is None:
        print("Setup cancelled.")
        return None
    return GitHubStorageConfig(
        repo_url=repo_url,
        token=token,
        branch=prev.branch if prev else "main",
        subdirectory=prev.subdirectory if prev else "",
    )


def _print_existing(storage: StorageConfig) -> None:
    if isinstance(storage, LocalStorageConfig):
        print("  type = local")
        print(f"  path = {storage.path}\n")
    elif isinstance(storage, GitHubStorageConfig):
        print("  type = github")
        print(f"  repo_url     = {storage.repo_url}")
        print(f"  branch       = {storage.branch}")
        print(f"  subdirectory = {storage.subdirectory or '(root)'}")
        token_state = "set" if storage.token else f"unset (uses ${TOKEN_ENV_VAR})"
        print(f"  token        = {token_state}\n")


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


def _nonempty(value: str) -> bool | str:
    return True if value.strip() else "Cannot be empty."
