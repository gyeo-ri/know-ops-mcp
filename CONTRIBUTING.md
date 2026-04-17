# Contributing

Thanks for your interest. This guide captures the conventions this repo follows so you can land changes quickly.

## Development setup

```bash
git clone https://github.com/gyeo-ri/cursor-memo-re
cd cursor-memo-re
uv sync --dev
```

`uv sync --dev` installs runtime + dev dependencies (currently just `pytest`).

To exercise the CLI from your checkout:

```bash
uv run know-ops-mcp setup
uv run know-ops-mcp serve
```

## Running tests

```bash
# everything (default scope)
uv run pytest

# one file
uv run pytest tests/storage/test_disk.py

# one test
uv run pytest tests/storage/test_disk.py::test_write_overwrites_existing

# include tests that hit real external services (GitHub, etc.)
uv run pytest -m live
```

The `live` marker is for tests that require network access and credentials (e.g. a real `KNOW_OPS_MCP_GITHUB_TOKEN`). They are excluded from the default run; opt in explicitly with `-m live`.

## Adding tests

- Mirror the source tree under `tests/`. `know_ops_mcp/storage/cache.py` → `tests/storage/test_cache.py`.
- File name is `test_*.py`; test function name is `test_*`.
- Filesystem I/O uses pytest's `tmp_path` fixture, never the real `~`.
- Environment variables and shells of state use `monkeypatch` so tests don't leak into each other (`monkeypatch.setenv`, `monkeypatch.delenv`).
- HTTP-touching code uses `respx` (added in T2) to mock `httpx` traffic.
- Any test that depends on network or credentials must be marked `@pytest.mark.live`.

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
- `docs:` README / PLANS / FEATURES / HISTORY / CONTRIBUTING
- `test:` test-only changes
- `chore:` deps, build config, tooling

Optional scope: `feat(setup): ...`, `fix(storage): ...`.

Subject is imperative and lowercase after the prefix. Body explains *why*, not *what* (the diff already shows what). Wrap large changes into multiple logically-scoped commits rather than one mega commit; reviewers and `git bisect` both benefit.

## Documenting design changes

Substantive design choices land as a numbered milestone in [HISTORY.md](HISTORY.md):

```
## M<N>. <one-line title>

<context: what triggered the change>

- 검토한 대안: <option> — <why rejected>
- 채택한 패턴: <decision>
- 인정한 trade-off: <known downside + mitigation>
```

Use this for: storage layer changes, configuration model changes, distribution/install model changes, any new third-party dependency.

Routine refactors and bug fixes don't need a HISTORY entry — the commit message is enough.

## Pull requests

- Branch from `main`.
- Prefer many small focused commits to one giant commit. If the diff covers multiple concerns, split it.
- If the change motivates a HISTORY milestone, link it from the PR description.
- Run `uv run pytest` before pushing.
- Keep `README.md`, `PLANS.md`, `FEATURES.md` honest — if your change makes them stale, update them in the same PR.
