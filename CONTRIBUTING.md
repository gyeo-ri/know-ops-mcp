# Contributing

Thanks for your interest. This guide captures the conventions this repo follows so you can land changes quickly.

## Development setup

```bash
git clone https://github.com/gyeo-ri/know-ops-mcp
cd know-ops-mcp
uv sync --dev
```

`uv sync --dev` installs runtime + dev dependencies (`pytest`, `pytest-httpx`).

To exercise the CLI from your checkout:

```bash
uv run know-ops-mcp setup
uv run know-ops-mcp serve
```

## Running tests

```bash
uv run pytest
```

All tests are offline; the GitHub backend is mocked with `pytest-httpx`. See [tests/README.md](tests/README.md) for layout and fixture conventions.

## Code conventions

- **Pydantic for models.** Discriminated unions for variant types (see `know_ops_mcp/setup/config.py:StorageConfig`).
- **No speculative classes or branches.** Don't add abstractions, helpers, or config knobs for hypothetical future needs. Add them when the second concrete caller appears.
- **No narrative comments.** Comments explain non-obvious intent or trade-offs only. Skip "Increment counter", "Return result", "Define class" style.
- **Storage backend additions** subclass either `InternalStorage` (no external dependencies) or `ExternalStorage` (network/service calls; must implement `list_versions`). Wrap external backends in `CachedStorage` at the composition layer (see `Config.to_storage_backend`).
- **Side-effect boundary.** Code may write under `~/.config/know-ops-mcp/`, `~/.cache/know-ops-mcp/`, the user-configured storage path, and the configured GitHub repo. Anything else (other tools' configs, shell rc files, system locations) is off-limits — even reads.

## Commit conventions

[Conventional Commits](https://www.conventionalcommits.org) prefix:

- `feat:` user-visible new behavior
- `fix:` bug fix
- `refactor:` internal restructure with no behavior change
- `docs:` README / AGENTS / CONTRIBUTING
- `test:` test-only changes
- `chore:` deps, build config, tooling

Optional scope: `feat(setup): ...`, `fix(storage): ...`.

Subject is imperative and lowercase after the prefix. Body explains *why*, not *what* (the diff already shows what). Wrap large changes into multiple logically-scoped commits rather than one mega commit; reviewers and `git bisect` both benefit.

## Documenting design changes

Substantive design choices land as a numbered milestone in the personal knowledge store
(entry `know-ops-mcp-history`, keyed by `M<N>`). Use this for: storage layer changes,
configuration model changes, distribution/install model changes, any new third-party dependency.

Routine refactors and bug fixes don't need a milestone — the commit message is enough.

## Pull requests

- Branch from `main`.
- Prefer many small focused commits to one giant commit. If the diff covers multiple concerns, split it.
- If the change motivates a CHANGELOG milestone, link it from the PR description.
- Run `uv run pytest` before pushing.
- Keep `README.md` and `AGENTS.md` honest — if your change makes them stale, update them in the same PR.
