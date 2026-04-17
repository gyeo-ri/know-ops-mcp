# know-ops-mcp

Shared knowledge MCP server for any LLM client. Stores entries as plain `.md` files with frontmatter, so you can read, edit, and version-control them outside the tool.

Two backends: a local directory for single-machine use, or a GitHub repository for syncing across multiple machines.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — provides `uvx`, which both launches the server and installs/manages its Python environment on first run.
- An MCP-compatible client (Cursor, Claude Desktop, Continue, ...)

Don't have `uv` yet? Install it first:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Other install methods (Homebrew, winget, pipx, ...) are listed at <https://docs.astral.sh/uv/getting-started/installation/>.

If any command below errors with `command not found: uvx`, you skipped this step.

## First-time setup

Run the interactive wizard once. Pick whichever invocation matches your install:

```bash
# Not yet on PyPI — use the git URL form for now:
uvx --from git+https://github.com/gyeo-ri/cursor-memo-re know-ops-mcp setup

# Once published to PyPI:
uvx know-ops-mcp setup
```

It will:

1. Ask which backend to use (`local` or `github`)
2. Ask backend-specific questions (path, or repo URL + token)
3. Save your config to `~/.config/know-ops-mcp/config.toml` with mode `0600`
4. Print an MCP registration snippet — already shaped for your install (it auto-detects whether you're on PyPI, a git URL, or a local checkout) — that you copy into your client's config

The snippet looks like this (PyPI form):

```json
{
  "mcpServers": {
    "know-ops-mcp": {
      "command": "uvx",
      "args": ["know-ops-mcp"]
    }
  }
}
```

…or like this if you ran setup via the git URL above:

```json
{
  "mcpServers": {
    "know-ops-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/gyeo-ri/cursor-memo-re",
        "know-ops-mcp"
      ]
    }
  }
}
```

Paste it into your MCP client's config file, then restart the client.
Common config locations (consult your client's documentation if unsure):

- **Cursor**: `~/.cursor/mcp.json`
- **Other clients**: see your client's MCP setup docs

## GitHub backend (multi-device sync)

Pick `github` during setup to share a single knowledge base across machines.
The wizard asks for two things:

- **Repo URL** — full URL like `https://github.com/yourname/your-knowledge-repo`. Create the repo first (private is fine).
- **Token** — a GitHub Personal Access Token with `repo` scope (or `contents:write` for fine-grained tokens).

The token is written to `~/.config/know-ops-mcp/config.toml` (mode `0600`).
If you prefer not to persist it on disk, leave the prompt blank and export it as an environment variable instead:

```bash
export KNOW_OPS_MCP_GITHUB_TOKEN=ghp_xxx
```

The env var takes precedence over the config value when both are set.
Branch defaults to `main` and subdirectory to the repo root; edit `config.toml` directly to change them.

### Caching

GitHub reads are cached under `~/.cache/know-ops-mcp/` (XDG-aware) so repeated lookups don't hit the API. Writes are immediately reflected in the cache. The cache has no expiry — use the `refresh_knowledge_cache` tool to invalidate it after another machine (or you yourself, via the GitHub web UI / git push) modifies an entry. You can ask the LLM to "refresh the knowledge cache" or "refresh `<knowledge_key>`" to trigger this.

## Verify

After restarting your client, six MCP tools should be available:

- `search_knowledge`
- `read_knowledge`
- `write_knowledge`
- `list_knowledge`
- `delete_knowledge`
- `refresh_knowledge_cache`

Try asking the LLM to write a note, then ask another session to read it back.

## Re-running setup

`know-ops-mcp setup` is idempotent and doubles as a status check.

- Answer **yes** to the modify prompt → change backend or update fields.
- Answer **no** → the wizard just prints your current config and the registration snippet, then exits without changes.

## Commands

Prefix each with `uvx --from <source>` (or just `uvx` once on PyPI), matching the install you used above.

| Command | What it does |
| --- | --- |
| `know-ops-mcp` | Same as `serve`. This is what your MCP client invokes as a subprocess. |
| `know-ops-mcp serve` | Run the MCP server over stdio. |
| `know-ops-mcp setup` | Interactive wizard. Re-run anytime to view or change config. |

## Storage layout

Each entry is one Markdown file with YAML frontmatter:

```yaml
---
knowledge_key: python-async-patterns
type: general
title: Python async patterns
description: One-line summary used for search and LLM relevance ranking.
tags: [python, async]
created: '2026-04-15'
updated: '2026-04-15'
---

Free-form Markdown body.
```

`knowledge_key` supports forward slashes for hierarchical organization (like S3 keys):

```
python-async-patterns          # flat key
know-ops-mcp/history           # project-scoped
coding-style/python/linting    # multi-level nesting
```

On disk and in GitHub, slashes become directory separators (`know-ops-mcp/history.md`). Use `list_knowledge(prefix="know-ops-mcp/")` to list entries under a specific path.

For the local backend, files live under the storage directory you chose during setup (named `<knowledge_key>.md`). The default is `$XDG_DATA_HOME/know-ops-mcp` (typically `~/.local/share/know-ops-mcp`); you can override it at the prompt.
For the GitHub backend, the same files live in your repo (under the configured subdirectory, root by default), and a content-addressed copy is mirrored under `~/.cache/know-ops-mcp/`.

## Scope and design

- **Client-agnostic.** This server speaks MCP over stdio. It does not know or care which LLM client connects to it.
- **No external side effects.** The tool only writes to its own config dir (`$XDG_CONFIG_HOME/know-ops-mcp/`), its cache dir (`$XDG_CACHE_HOME/know-ops-mcp/`), and the storage backend you configured. It never modifies your client's `mcp.json` or any other external file.
- **XDG-aware paths.** Config, cache, and the local backend default all follow the XDG Base Directory specification (`~/.config`, `~/.cache`, `~/.local/share`).

## Documentation

- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Agent context: [AGENTS.md](AGENTS.md)

## Development

```bash
git clone https://github.com/gyeo-ri/cursor-memo-re
cd cursor-memo-re
uv sync --dev
uv run know-ops-mcp setup
uv run pytest
```

The wizard will detect that you're running from a local checkout and produce a snippet using `uvx --from /absolute/path/to/checkout know-ops-mcp` so changes you make under the checkout are picked up immediately on the next MCP server spawn.

For testing conventions, commit style, and PR workflow, see [CONTRIBUTING.md](CONTRIBUTING.md).
