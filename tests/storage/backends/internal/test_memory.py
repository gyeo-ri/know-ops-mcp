from know_ops_mcp.storage.backends.internal.memory import MemoryStorage


def test_read_missing_returns_none():
    assert MemoryStorage().read("nope") is None


def test_write_then_read():
    s = MemoryStorage()
    s.write("a", "alpha")
    assert s.read("a") == "alpha"


def test_overwrite():
    s = MemoryStorage()
    s.write("a", "v1")
    s.write("a", "v2")
    assert s.read("a") == "v2"


def test_delete_present_returns_true():
    s = MemoryStorage()
    s.write("a", "alpha")
    assert s.delete("a") is True
    assert s.read("a") is None


def test_delete_absent_returns_false():
    assert MemoryStorage().delete("a") is False


def test_list_all_isolates_internal_state():
    s = MemoryStorage()
    s.write("a", "alpha")
    snap = s.list_all()
    snap["mutated"] = "external"
    assert "mutated" not in s.list_all()
