# Tests

```bash
uv run pytest                       # full suite
uv run pytest -v                    # verbose
uv run pytest tests/storage         # subset
uv run pytest tests/storage/test_disk.py::test_write_overwrites_existing
```

All tests are offline. The GitHub backend is exercised through `respx`-mocked HTTP, not real API calls. Verifying against the real GitHub API is a manual step done before a release.

## Adding tests

| Concern | Tool / convention |
| --- | --- |
| Layout | Mirror `know_ops_mcp/`. `know_ops_mcp/storage/cache.py` → `tests/storage/test_cache.py` |
| File / function names | `test_*.py`, `test_*` |
| Filesystem I/O | `tmp_path` fixture, never the real `~` |
| Env vars | `monkeypatch.setenv` / `monkeypatch.delenv` |
| `httpx` traffic | `respx` (`@respx.mock`) |

See [../CONTRIBUTING.md](../CONTRIBUTING.md) for code conventions, commit style, and PR flow.
