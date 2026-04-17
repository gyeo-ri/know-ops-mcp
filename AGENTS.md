# AGENTS.md

Shared-knowledge MCP server for LLM clients. Python + fastmcp. Pre-PyPI, single-user daily use.

## Other docs

- `README.md` — user-facing install/run guide
- `CHANGELOG.md` — every design decision with rationale, indexed by `M<n>`. Search this before making a non-trivial change to avoid re-litigating settled questions.
- `CONTRIBUTING.md` — commit and style conventions
- `docs/ARCHITECTURE.md` — current architecture and per-module contracts
- `docs/ROADMAP.md` — open TODOs (id-keyed) and rejected alternatives
- `tests/README.md` — test layout and conventions

## Hard rules

- **Never modify external files.** No writes to `~/.cursor/mcp.json`, Claude Desktop config, or any other tool's settings — not even reads. We emit snippets for the user to paste. (CHANGELOG M11)
- **Stay client-agnostic.** This repo is an MCP server; it must not detect, branch on, or care which LLM client is calling it. (CHANGELOG M12)
- **No speculative code.** Don't add classes/abstractions/branches for use cases we don't have today.
- **No narration comments.** Don't write comments that just restate what the code does.

## Update obligations

When you change behavior, update the corresponding doc in the same commit/PR:

- New or removed module/feature → `docs/ARCHITECTURE.md`
- Design decision or accepted/rejected trade-off → new milestone in `CHANGELOG.md` (`M<n>`)
- Roadmap status change (start/finish/block an item, add a new one) → `docs/ROADMAP.md`
- Behavior change → tests in `tests/`

## Workflow

1. Before non-trivial changes, grep `CHANGELOG.md` for related keywords to surface prior decisions.
2. Keep commits small and focused. See `CONTRIBUTING.md` for style.
3. Wait for user approval before moving to the next step.
