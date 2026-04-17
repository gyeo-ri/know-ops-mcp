# know-ops-mcp

Shared knowledge MCP server for any LLM client. Stores entries as plain `.md` files with frontmatter, so you can read, edit, and version-control them outside the tool.

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

1. Ask for a storage directory (default `~/Documents/know-ops-mcp`)
2. Save your config to `~/.config/know-ops-mcp/config.toml`
3. Print an MCP registration snippet that you copy into your client's config

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

## Verify

After restarting your client, five MCP tools should be available:

- `search_knowledge`
- `read_knowledge`
- `write_knowledge`
- `list_knowledge`
- `delete_knowledge`

Try asking the LLM to write a note, then ask another session to read it back.

## Re-running setup

`know-ops-mcp setup` is idempotent and doubles as a status check.

- Answer **yes** to the modify prompt → change the storage path.
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

Files live under the storage directory you chose during setup, named `<unique_name>.md`.

## Scope and design

- **Client-agnostic.** This server speaks MCP over stdio. It does not know or care which LLM client connects to it.
- **No external side effects.** The tool only writes to its own config dir (`~/.config/know-ops-mcp/`) and the storage directory you chose. It never modifies your client's `mcp.json` or any other external file.

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
