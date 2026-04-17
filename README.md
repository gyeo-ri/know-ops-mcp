# know-ops-mcp

Shared knowledge MCP server for any LLM client. Stores entries as plain `.md` files with frontmatter, so you can read, edit, and version-control them outside the tool.

Two backends: a local directory for single-machine use, or a GitHub repository for syncing across multiple machines.

## Requirements

- Python 3.11+
- An MCP-compatible client (Cursor, Claude Desktop, Continue, ...)

## Install

```bash
uv tool install know-ops-mcp
# or
pip install know-ops-mcp
```

## First-time setup

Run the interactive wizard once:

```bash
know-ops-mcp setup
```

It will:

1. Ask which backend to use (`local` or `github`)
2. Ask backend-specific questions (path, or repo URL + token)
3. Save your config to `~/.config/know-ops-mcp/config.toml` with mode `0600`
4. Print an MCP registration snippet that you copy into your client's config

The snippet looks like this:

```json
{
  "mcpServers": {
    "know-ops-mcp": {
      "command": "know-ops-mcp"
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

GitHub reads are cached under `~/.cache/know-ops-mcp/` (XDG-aware) so repeated lookups don't hit the API. Writes are immediately reflected in the cache. The cache has no expiry — use the `refresh_knowledge_cache` tool to invalidate it after another machine (or you yourself, via the GitHub web UI / git push) modifies an entry. You can ask the LLM to "refresh the knowledge cache" or "refresh `<unique_name>`" to trigger this.

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

| Command | What it does |
| --- | --- |
| `know-ops-mcp` | Same as `serve`. This is what your MCP client invokes as a subprocess. |
| `know-ops-mcp serve` | Run the MCP server over stdio. |
| `know-ops-mcp setup` | Interactive wizard. Re-run anytime to view or change config. |

## Storage layout

Each entry is one Markdown file with YAML frontmatter:

```yaml
---
unique_name: python-async-patterns
type: general
title: Python async patterns
description: One-line summary used for search and LLM relevance ranking.
tags: [python, async]
created: '2026-04-15'
updated: '2026-04-15'
---

Free-form Markdown body.
```

For the local backend, files live under the storage directory you chose (named `<unique_name>.md`).
For the GitHub backend, the same files live in your repo (under the configured subdirectory, root by default), and a content-addressed copy is mirrored under `~/.cache/know-ops-mcp/`.

## Scope and design

- **Client-agnostic.** This server speaks MCP over stdio. It does not know or care which LLM client connects to it.
- **No external side effects.** The tool only writes to its own config dir (`~/.config/know-ops-mcp/`), its cache dir (`~/.cache/know-ops-mcp/`), and the storage backend you configured. It never modifies your client's `mcp.json` or any other external file.

## Documentation

- Architecture and roadmap: [PLANS.md](PLANS.md)
- Implemented features: [FEATURES.md](FEATURES.md)
- Change history: [HISTORY.md](HISTORY.md)

## Development

```bash
git clone <repo-url> cursor-memo-re
cd cursor-memo-re
uv sync
uv run know-ops-mcp setup
```
