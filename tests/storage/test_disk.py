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


def test_list_all_skips_uppercase_md_files(tmp_path):
    disk.write(tmp_path, "entry", "body")
    (tmp_path / "README.md").write_text("# Readme")
    (tmp_path / "LICENSE.md").write_text("MIT")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "CONTRIBUTING.md").write_text("# Contributing")
    assert disk.list_all(tmp_path) == {"entry": "body"}


def test_clear_removes_only_md_files(tmp_path):
    disk.write(tmp_path, "a", "alpha")
    disk.write(tmp_path, "b", "beta")
    (tmp_path / "keep.txt").write_text("preserve")
    disk.clear(tmp_path)
    assert disk.list_all(tmp_path) == {}
    assert (tmp_path / "keep.txt").is_file()


class TestNestedPaths:
    def test_write_creates_subdirectories(self, tmp_path):
        disk.write(tmp_path, "project/topic", "body")
        assert (tmp_path / "project" / "topic.md").is_file()

    def test_read_nested(self, tmp_path):
        disk.write(tmp_path, "a/b/c", "deep")
        assert disk.read(tmp_path, "a/b/c") == "deep"

    def test_list_all_returns_slash_keys(self, tmp_path):
        disk.write(tmp_path, "flat", "f")
        disk.write(tmp_path, "dir/nested", "n")
        disk.write(tmp_path, "dir/sub/deep", "d")
        result = disk.list_all(tmp_path)
        assert result == {"flat": "f", "dir/nested": "n", "dir/sub/deep": "d"}

    def test_delete_nested_prunes_empty_parents(self, tmp_path):
        disk.write(tmp_path, "a/b/c", "body")
        assert disk.delete(tmp_path, "a/b/c") is True
        assert not (tmp_path / "a").exists()

    def test_delete_nested_keeps_non_empty_parents(self, tmp_path):
        disk.write(tmp_path, "a/b", "keep")
        disk.write(tmp_path, "a/c", "remove")
        disk.delete(tmp_path, "a/c")
        assert (tmp_path / "a").is_dir()
        assert disk.read(tmp_path, "a/b") == "keep"

    def test_clear_removes_nested_md_and_prunes_dirs(self, tmp_path):
        disk.write(tmp_path, "x/y", "body")
        disk.write(tmp_path, "x/z/w", "body2")
        disk.clear(tmp_path)
        assert disk.list_all(tmp_path) == {}
        assert not (tmp_path / "x").exists()
