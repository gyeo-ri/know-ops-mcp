# AGENTS.md

Shared-knowledge MCP server for LLM clients. Python + fastmcp. Pre-PyPI, single-user daily use.

## Docs in this repo

- `README.md` — user-facing install/run guide
- `CONTRIBUTING.md` — commit and style conventions
- `tests/README.md` — test layout and conventions

Design decisions, roadmap, and detailed architecture are in the personal knowledge store
(`know-ops-mcp-history`, `know-ops-mcp-roadmap`, `know-ops-mcp-overview`, `know-ops-mcp-architecture`).
Search them via `search_knowledge` / `read_knowledge` before making non-trivial changes.

## Hard rules

- **Never modify external files.** No writes to `~/.cursor/mcp.json`, Claude Desktop config, or any other tool's settings — not even reads. We emit snippets for the user to paste.
- **Stay client-agnostic.** This repo is an MCP server; it must not detect, branch on, or care which LLM client is calling it.
- **No speculative code.** Don't add classes/abstractions/branches for use cases we don't have today.
- **No narration comments.** Don't write comments that just restate what the code does.

## Update obligations

When you change behavior, update in the same commit/PR:

- Behavior change → tests in `tests/`
- New or removed module/feature → this file (if it affects a hard rule or obligation)
- Design decision or trade-off → new milestone in personal store (`know-ops-mcp-history`, key `M<n>`)

## Workflow

1. Before non-trivial changes, `read_knowledge("know-ops-mcp-history")` to surface prior decisions.
2. Keep commits small and focused. See `CONTRIBUTING.md` for style.
3. Wait for user approval before moving to the next step.
