import pytest

from know_ops_mcp.storage import disk
from know_ops_mcp.storage.backends.external import ExternalStorage
from know_ops_mcp.storage.cache import CachedStorage, default_cache_dir


class _FakeExternal(ExternalStorage):
    """In-memory ExternalStorage with call recording for cache assertions."""

    def __init__(self, initial: dict[str, str] | None = None) -> None:
        self._data: dict[str, str] = dict(initial or {})
        self.read_calls: list[str] = []
        self.write_calls: list[tuple[str, str]] = []
        self.delete_calls: list[str] = []
        self.list_versions_calls = 0

    def read(self, name: str) -> str | None:
        self.read_calls.append(name)
        return self._data.get(name)

    def write(self, name: str, content: str) -> None:
        self.write_calls.append((name, content))
        self._data[name] = content

    def delete(self, name: str) -> bool:
        self.delete_calls.append(name)
        return self._data.pop(name, None) is not None

    def list_all(self) -> dict[str, str]:
        return dict(self._data)

    def list_versions(self) -> dict[str, str]:
        self.list_versions_calls += 1
        return {name: f"sha-{name}" for name in self._data}


@pytest.fixture
def fake():
    return _FakeExternal({"alpha": "alpha-body", "beta": "beta-body"})


@pytest.fixture
def cache(fake, tmp_path):
    return CachedStorage(fake, cache_dir=tmp_path)


def test_read_miss_populates_cache(fake, cache, tmp_path):
    assert cache.read("alpha") == "alpha-body"
    assert fake.read_calls == ["alpha"]
    assert (tmp_path / "alpha.md").read_text() == "alpha-body"


def test_read_hit_skips_backend(fake, cache):
    cache.read("alpha")
    fake.read_calls.clear()

    assert cache.read("alpha") == "alpha-body"
    assert fake.read_calls == []


def test_read_missing_does_not_create_cache_file(fake, cache, tmp_path):
    assert cache.read("ghost") is None
    assert not (tmp_path / "ghost.md").exists()


def test_write_is_write_through(fake, cache, tmp_path):
    cache.write("gamma", "gamma-body")
    assert fake.write_calls == [("gamma", "gamma-body")]
    assert (tmp_path / "gamma.md").read_text() == "gamma-body"


def test_write_then_read_serves_from_cache(fake, cache):
    cache.write("gamma", "gamma-body")
    fake.read_calls.clear()
    assert cache.read("gamma") == "gamma-body"
    assert fake.read_calls == []


def test_delete_evicts_cache_and_hits_backend(fake, cache, tmp_path):
    cache.read("alpha")
    assert cache.delete("alpha") is True
    assert fake.delete_calls == ["alpha"]
    assert not (tmp_path / "alpha.md").exists()


def test_delete_returns_backend_result_when_absent(fake, cache):
    assert cache.delete("ghost") is False


def test_delete_evicts_cache_even_if_backend_fails_silently(fake, cache, tmp_path):
    cache.write("temp", "tmp-body")
    fake._data.pop("temp")
    assert cache.delete("temp") is False
    assert not (tmp_path / "temp.md").exists()


def test_list_all_uses_list_versions_then_caches_per_entry(fake, cache, tmp_path):
    result = cache.list_all()
    assert result == {"alpha": "alpha-body", "beta": "beta-body"}
    assert fake.list_versions_calls == 1
    assert sorted(fake.read_calls) == ["alpha", "beta"]
    assert (tmp_path / "alpha.md").exists()
    assert (tmp_path / "beta.md").exists()


def test_list_all_second_call_skips_per_entry_backend_reads(fake, cache):
    cache.list_all()
    fake.read_calls.clear()
    cache.list_all()
    assert fake.read_calls == []
    assert fake.list_versions_calls == 2


def test_list_all_picks_up_new_remote_entry(fake, cache):
    cache.list_all()
    fake._data["delta"] = "delta-body"
    result = cache.list_all()
    assert "delta" in result and result["delta"] == "delta-body"


def test_refresh_targeted_evicts_only_named_entry(fake, cache, tmp_path):
    cache.read("alpha")
    cache.read("beta")
    cache.refresh("alpha")
    assert not (tmp_path / "alpha.md").exists()
    assert (tmp_path / "beta.md").exists()


def test_refresh_all_clears_cache(fake, cache, tmp_path):
    cache.read("alpha")
    cache.read("beta")
    cache.refresh()
    assert list(tmp_path.glob("*.md")) == []


def test_refresh_then_read_refetches_and_recaches(fake, cache, tmp_path):
    cache.read("alpha")
    cache.refresh("alpha")
    fake.read_calls.clear()

    cache.read("alpha")
    assert fake.read_calls == ["alpha"]
    assert (tmp_path / "alpha.md").exists()


def test_refresh_after_remote_change_surfaces_new_content(fake, cache):
    cache.read("alpha")
    fake._data["alpha"] = "alpha-body-v2"
    assert cache.read("alpha") == "alpha-body"
    cache.refresh("alpha")
    assert cache.read("alpha") == "alpha-body-v2"


def test_default_cache_dir_uses_xdg_when_set(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert default_cache_dir() == tmp_path / "know-ops-mcp"


def test_default_cache_dir_falls_back_to_home_cache(monkeypatch):
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    result = default_cache_dir()
    assert result.name == "know-ops-mcp"
    assert result.parent.name == ".cache"


def test_init_creates_cache_dir(fake, tmp_path):
    target = tmp_path / "nested" / "cache"
    CachedStorage(fake, cache_dir=target)
    assert target.is_dir()


def test_uses_disk_helpers_for_cache_io(fake, cache, tmp_path):
    cache.write("x", "y")
    assert disk.read(tmp_path, "x") == "y"
