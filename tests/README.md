---
purpose: 테스트 작성/실행 컨벤션
audience: [humans, agents]
update_when: 테스트 도구/패턴/슈트 구조 변경 시
---

# Tests

```bash
uv run pytest                       # full suite
uv run pytest -v                    # verbose
uv run pytest tests/storage         # subset
uv run pytest tests/storage/test_disk.py::test_write_overwrites_existing
```

All tests are offline. The GitHub backend is exercised through `pytest-httpx`-mocked HTTP, not real API calls. Verifying against the real GitHub API is a manual step done before a release.

## Adding tests

| Concern | Tool / convention |
| --- | --- |
| Layout | Mirror `know_ops_mcp/`. `know_ops_mcp/storage/cache.py` → `tests/storage/test_cache.py` |
| File / function names | `test_*.py`, `test_*` |
| Filesystem I/O | `tmp_path` fixture, never the real `~` |
| Env vars | `monkeypatch.setenv` / `monkeypatch.delenv` |
| `httpx` traffic | `pytest-httpx` (`httpx_mock` fixture) |

See [../CONTRIBUTING.md](../CONTRIBUTING.md) for code conventions, commit style, and PR flow.
