from know_ops_mcp.storage import disk


def test_ensure_creates_nested_dirs(tmp_path):
    target = tmp_path / "a" / "b" / "c"
    disk.ensure(target)
    assert target.is_dir()


def test_ensure_is_idempotent(tmp_path):
    target = tmp_path / "x"
    disk.ensure(target)
    disk.ensure(target)
    assert target.is_dir()


def test_read_returns_none_for_missing(tmp_path):
    assert disk.read(tmp_path, "absent") is None


def test_write_then_read_round_trip(tmp_path):
    disk.write(tmp_path, "hello", "world")
    assert disk.read(tmp_path, "hello") == "world"


def test_write_creates_md_file(tmp_path):
    disk.write(tmp_path, "entry", "body")
    assert (tmp_path / "entry.md").is_file()


def test_write_does_not_leave_tmp_artifact(tmp_path):
    disk.write(tmp_path, "entry", "body")
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []


def test_write_overwrites_existing(tmp_path):
    disk.write(tmp_path, "entry", "v1")
    disk.write(tmp_path, "entry", "v2")
    assert disk.read(tmp_path, "entry") == "v2"


def test_delete_returns_true_when_present(tmp_path):
    disk.write(tmp_path, "entry", "body")
    assert disk.delete(tmp_path, "entry") is True
    assert disk.read(tmp_path, "entry") is None


def test_delete_returns_false_when_absent(tmp_path):
    assert disk.delete(tmp_path, "absent") is False


def test_list_all_returns_name_to_content(tmp_path):
    disk.write(tmp_path, "a", "alpha")
    disk.write(tmp_path, "b", "beta")
    assert disk.list_all(tmp_path) == {"a": "alpha", "b": "beta"}


def test_list_all_empty_dir_returns_empty(tmp_path):
    assert disk.list_all(tmp_path) == {}


def test_list_all_ignores_non_md_files(tmp_path):
    disk.write(tmp_path, "kept", "yes")
    (tmp_path / "noise.txt").write_text("ignored")
    (tmp_path / "kept.md.tmp").write_text("ignored")
    assert disk.list_all(tmp_path) == {"kept": "yes"}


def test_clear_removes_only_md_files(tmp_path):
    disk.write(tmp_path, "a", "alpha")
    disk.write(tmp_path, "b", "beta")
    (tmp_path / "keep.txt").write_text("preserve")
    disk.clear(tmp_path)
    assert disk.list_all(tmp_path) == {}
    assert (tmp_path / "keep.txt").is_file()
