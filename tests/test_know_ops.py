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
        knowledge_key="alpha",
        title="Alpha title",
        description="Alpha description",
        content="alpha body",
        tags=["t1"],
    )
    defaults.update(overrides)
    ops.write(**defaults)
    return defaults["knowledge_key"]


class TestWrite:
    def test_creates_new_entry_with_today_dates(self, ops):
        knowledge = ops.write(
            knowledge_key="x",
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
        ops.write(knowledge_key="x", title="T", description="D", content="v1")

        class _FakeDate2:
            @staticmethod
            def today():
                class _D:
                    @staticmethod
                    def isoformat():
                        return "2026-04-15"
                return _D()

        monkeypatch.setattr(ko_mod, "date", _FakeDate2)
        updated = ops.write(knowledge_key="x", title="T2", description="D2", content="v2")
        assert updated.created == "2020-01-01"
        assert updated.updated == "2026-04-15"
        assert updated.title == "T2"
        assert updated.content == "v2"

    def test_unknown_type_raises_value_error(self, ops):
        with pytest.raises(ValueError, match="Unknown knowledge type"):
            ops.write(
                knowledge_key="x", title="T", description="D", content="C", type="nope"
            )

    def test_invalid_knowledge_key_raises_validation_error(self, ops):
        with pytest.raises(ValidationError):
            ops.write(knowledge_key="Bad Name", title="T", description="D", content="C")


class TestRead:
    def test_missing_returns_none(self, ops):
        assert ops.read("missing") is None

    def test_existing_returns_knowledge(self, ops):
        _seed(ops)
        result = ops.read("alpha")
        assert result is not None
        assert result.knowledge_key == "alpha"
        assert result.content == "alpha body"


class TestSearch:
    def test_empty_query_matches_all(self, ops):
        _seed(ops, knowledge_key="a")
        _seed(ops, knowledge_key="b")
        assert len(ops.search("")) == 2

    def test_keyword_in_title(self, ops):
        _seed(ops, knowledge_key="a", title="Pizza recipe")
        _seed(ops, knowledge_key="b", title="Salad recipe")
        results = ops.search("pizza")
        assert [r["knowledge_key"] for r in results] == ["a"]

    def test_keyword_in_content(self, ops):
        _seed(ops, knowledge_key="a", content="contains pineapple")
        _seed(ops, knowledge_key="b", content="just cheese")
        results = ops.search("pineapple")
        assert [r["knowledge_key"] for r in results] == ["a"]

    def test_case_insensitive(self, ops):
        _seed(ops, knowledge_key="a", title="UPPERCASE")
        results = ops.search("uppercase")
        assert len(results) == 1

    def test_tags_filter_intersection(self, ops):
        _seed(ops, knowledge_key="a", tags=["work", "urgent"])
        _seed(ops, knowledge_key="b", tags=["personal"])
        _seed(ops, knowledge_key="c", tags=["work"])
        results = ops.search("", tags=["work"])
        assert {r["knowledge_key"] for r in results} == {"a", "c"}

    def test_limit_truncates(self, ops):
        for i in range(5):
            _seed(ops, knowledge_key=f"e{i}")
        assert len(ops.search("", limit=2)) == 2


class TestListAll:
    def test_returns_summaries(self, ops):
        _seed(ops, knowledge_key="a")
        _seed(ops, knowledge_key="b")
        results = ops.list_all()
        names = {r["knowledge_key"] for r in results}
        assert names == {"a", "b"}
        assert all("content" not in r for r in results)

    def test_tag_filter(self, ops):
        _seed(ops, knowledge_key="a", tags=["x"])
        _seed(ops, knowledge_key="b", tags=["y"])
        results = ops.list_all(tag="x")
        assert [r["knowledge_key"] for r in results] == ["a"]

    def test_prefix_filter(self, ops):
        _seed(ops, knowledge_key="proj/alpha")
        _seed(ops, knowledge_key="proj/beta")
        _seed(ops, knowledge_key="other")
        results = ops.list_all(prefix="proj/")
        assert {r["knowledge_key"] for r in results} == {"proj/alpha", "proj/beta"}

    def test_prefix_and_tag_combined(self, ops):
        _seed(ops, knowledge_key="proj/a", tags=["x"])
        _seed(ops, knowledge_key="proj/b", tags=["y"])
        _seed(ops, knowledge_key="other", tags=["x"])
        results = ops.list_all(tag="x", prefix="proj/")
        assert [r["knowledge_key"] for r in results] == ["proj/a"]


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
