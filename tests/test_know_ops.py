from datetime import date

import pytest
from pydantic import ValidationError

from know_ops_mcp.know_ops import KnowOps
from know_ops_mcp.storage import StorageService
from know_ops_mcp.storage.backends.internal.memory import MemoryStorage


@pytest.fixture
def ops():
    return KnowOps(StorageService(MemoryStorage()))


def _seed(ops: KnowOps, **overrides) -> str:
    defaults = dict(
        unique_name="alpha",
        title="Alpha title",
        description="Alpha description",
        content="alpha body",
        tags=["t1"],
    )
    defaults.update(overrides)
    ops.write(**defaults)
    return defaults["unique_name"]


class TestWrite:
    def test_creates_new_entry_with_today_dates(self, ops):
        knowledge = ops.write(
            unique_name="x",
            title="T",
            description="D",
            content="C",
        )
        today = date.today().isoformat()
        assert knowledge.created == today
        assert knowledge.updated == today
        assert knowledge.type == "general"

    def test_update_preserves_created_changes_updated(self, ops, monkeypatch):
        import know_ops_mcp.know_ops as ko_mod

        class _FakeDate:
            @staticmethod
            def today():
                class _D:
                    @staticmethod
                    def isoformat():
                        return "2020-01-01"
                return _D()

        monkeypatch.setattr(ko_mod, "date", _FakeDate)
        ops.write(unique_name="x", title="T", description="D", content="v1")

        class _FakeDate2:
            @staticmethod
            def today():
                class _D:
                    @staticmethod
                    def isoformat():
                        return "2026-04-15"
                return _D()

        monkeypatch.setattr(ko_mod, "date", _FakeDate2)
        updated = ops.write(unique_name="x", title="T2", description="D2", content="v2")
        assert updated.created == "2020-01-01"
        assert updated.updated == "2026-04-15"
        assert updated.title == "T2"
        assert updated.content == "v2"

    def test_unknown_type_raises_value_error(self, ops):
        with pytest.raises(ValueError, match="Unknown knowledge type"):
            ops.write(
                unique_name="x", title="T", description="D", content="C", type="nope"
            )

    def test_invalid_unique_name_raises_validation_error(self, ops):
        with pytest.raises(ValidationError):
            ops.write(unique_name="Bad Name", title="T", description="D", content="C")


class TestRead:
    def test_missing_returns_none(self, ops):
        assert ops.read("missing") is None

    def test_existing_returns_knowledge(self, ops):
        _seed(ops)
        result = ops.read("alpha")
        assert result is not None
        assert result.unique_name == "alpha"
        assert result.content == "alpha body"


class TestSearch:
    def test_empty_query_matches_all(self, ops):
        _seed(ops, unique_name="a")
        _seed(ops, unique_name="b")
        assert len(ops.search("")) == 2

    def test_keyword_in_title(self, ops):
        _seed(ops, unique_name="a", title="Pizza recipe")
        _seed(ops, unique_name="b", title="Salad recipe")
        results = ops.search("pizza")
        assert [r["unique_name"] for r in results] == ["a"]

    def test_keyword_in_content(self, ops):
        _seed(ops, unique_name="a", content="contains pineapple")
        _seed(ops, unique_name="b", content="just cheese")
        results = ops.search("pineapple")
        assert [r["unique_name"] for r in results] == ["a"]

    def test_case_insensitive(self, ops):
        _seed(ops, unique_name="a", title="UPPERCASE")
        results = ops.search("uppercase")
        assert len(results) == 1

    def test_tags_filter_intersection(self, ops):
        _seed(ops, unique_name="a", tags=["work", "urgent"])
        _seed(ops, unique_name="b", tags=["personal"])
        _seed(ops, unique_name="c", tags=["work"])
        results = ops.search("", tags=["work"])
        assert {r["unique_name"] for r in results} == {"a", "c"}

    def test_limit_truncates(self, ops):
        for i in range(5):
            _seed(ops, unique_name=f"e{i}")
        assert len(ops.search("", limit=2)) == 2


class TestListAll:
    def test_returns_summaries(self, ops):
        _seed(ops, unique_name="a")
        _seed(ops, unique_name="b")
        results = ops.list_all()
        names = {r["unique_name"] for r in results}
        assert names == {"a", "b"}
        assert all("content" not in r for r in results)

    def test_tag_filter(self, ops):
        _seed(ops, unique_name="a", tags=["x"])
        _seed(ops, unique_name="b", tags=["y"])
        results = ops.list_all(tag="x")
        assert [r["unique_name"] for r in results] == ["a"]


class TestDelete:
    def test_existing_returns_true(self, ops):
        _seed(ops)
        assert ops.delete("alpha") is True
        assert ops.read("alpha") is None

    def test_missing_returns_false(self, ops):
        assert ops.delete("ghost") is False


class TestRefresh:
    def test_delegates_to_storage(self):
        calls: list[str | None] = []

        class _RecorderBackend(MemoryStorage):
            def refresh(self, name=None):
                calls.append(name)

        ops = KnowOps(StorageService(_RecorderBackend()))
        ops.refresh()
        ops.refresh("specific")
        assert calls == [None, "specific"]
