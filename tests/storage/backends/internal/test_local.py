import pytest

from know_ops_mcp.storage.backends.internal.local import (
    LocalDirectoryStorage,
    default_data_dir,
)


def test_init_creates_root_if_missing(tmp_path):
    target = tmp_path / "new" / "nested"
    LocalDirectoryStorage(target)
    assert target.is_dir()


def test_write_then_read(tmp_path):
    s = LocalDirectoryStorage(tmp_path)
    s.write("entry", "body")
    assert s.read("entry") == "body"


def test_read_missing(tmp_path):
    assert LocalDirectoryStorage(tmp_path).read("absent") is None


def test_delete_round_trip(tmp_path):
    s = LocalDirectoryStorage(tmp_path)
    s.write("entry", "body")
    assert s.delete("entry") is True
    assert s.read("entry") is None
    assert s.delete("entry") is False


def test_list_all_returns_all_entries(tmp_path):
    s = LocalDirectoryStorage(tmp_path)
    s.write("a", "alpha")
    s.write("b", "beta")
    assert s.list_all() == {"a": "alpha", "b": "beta"}


def test_two_instances_share_filesystem(tmp_path):
    a = LocalDirectoryStorage(tmp_path)
    a.write("entry", "body")
    b = LocalDirectoryStorage(tmp_path)
    assert b.read("entry") == "body"


def test_default_data_dir_uses_xdg_when_set(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert default_data_dir() == tmp_path / "know-ops-mcp"


def test_default_data_dir_falls_back_to_home_local_share(monkeypatch):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    result = default_data_dir()
    assert result.name == "know-ops-mcp"
    assert result.parent.name == "share"
    assert result.parent.parent.name == ".local"


@pytest.mark.parametrize("name,content", [
    ("ascii", "plain body"),
    ("unicode", "본문에 한글"),
    ("with-dash", "dash in name"),
    ("digits-123", "digits"),
])
def test_various_names_round_trip(tmp_path, name, content):
    s = LocalDirectoryStorage(tmp_path)
    s.write(name, content)
    assert s.read(name) == content
