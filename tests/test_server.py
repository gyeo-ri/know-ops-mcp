import json

import pytest

from know_ops_mcp import server
from know_ops_mcp.storage import storage
from know_ops_mcp.storage.backends.internal.memory import MemoryStorage


@pytest.fixture(autouse=True)
def fresh_storage():
    storage.configure(MemoryStorage())
    yield
    storage.configure(MemoryStorage())


def _seed(unique_name: str = "alpha", **overrides) -> None:
    payload = dict(
        unique_name=unique_name,
        title="T",
        description="D",
        content="C",
        tags=["t1"],
    )
    payload.update(overrides)
    server.write_knowledge(**payload)


class TestSearchTool:
    def test_no_match_returns_message(self):
        result = server.search_knowledge("nothing")
        assert result == "No knowledge entries found matching the query."

    def test_match_returns_json_summary_list(self):
        _seed("alpha", title="findme")
        result = server.search_knowledge("findme")
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["unique_name"] == "alpha"
        assert "content" not in parsed[0]


class TestReadTool:
    def test_missing_returns_message(self):
        assert server.read_knowledge("ghost") == "Knowledge 'ghost' not found."

    def test_existing_returns_full_json(self):
        _seed("alpha", content="body")
        parsed = json.loads(server.read_knowledge("alpha"))
        assert parsed["unique_name"] == "alpha"
        assert parsed["content"] == "body"


class TestWriteTool:
    def test_success_returns_full_json(self):
        result = server.write_knowledge(
            unique_name="alpha", title="T", description="D", content="C"
        )
        parsed = json.loads(result)
        assert parsed["unique_name"] == "alpha"
        assert parsed["type"] == "general"

    def test_invalid_unique_name_returns_validation_message(self):
        result = server.write_knowledge(
            unique_name="Bad Name", title="T", description="D", content="C"
        )
        assert result.startswith("Validation failed:")
        assert "unique_name" in result

    def test_unknown_type_returns_error_message(self):
        result = server.write_knowledge(
            unique_name="alpha",
            title="T",
            description="D",
            content="C",
            type="nope",
        )
        assert result.startswith("Error:")
        assert "Unknown knowledge type" in result


class TestListTool:
    def test_empty_returns_message(self):
        assert server.list_knowledge() == "No knowledge entries found."

    def test_returns_summaries_as_json(self):
        _seed("a")
        _seed("b")
        parsed = json.loads(server.list_knowledge())
        assert {p["unique_name"] for p in parsed} == {"a", "b"}

    def test_tag_filter(self):
        _seed("a", tags=["x"])
        _seed("b", tags=["y"])
        parsed = json.loads(server.list_knowledge(tag="x"))
        assert [p["unique_name"] for p in parsed] == ["a"]


class TestDeleteTool:
    def test_existing_returns_confirmation(self):
        _seed("alpha")
        assert server.delete_knowledge("alpha") == "Knowledge 'alpha' deleted."

    def test_missing_returns_not_found(self):
        assert server.delete_knowledge("ghost") == "Knowledge 'ghost' not found."


class TestRefreshTool:
    def test_without_name_message(self):
        assert server.refresh_knowledge_cache() == "Cache refreshed."

    def test_with_name_message(self):
        assert (
            server.refresh_knowledge_cache("alpha")
            == "Cache refreshed for 'alpha'."
        )


class TestBootstrap:
    def test_no_config_warns_and_keeps_default_backend(self, monkeypatch, capsys):
        from know_ops_mcp.setup.config import Config

        monkeypatch.setattr(Config, "load", classmethod(lambda cls: None))
        sentinel = MemoryStorage()
        storage.configure(sentinel)
        server.bootstrap()
        assert storage._backend is sentinel
        err = capsys.readouterr().err
        assert "No config found" in err

    def test_with_config_invokes_configure(self, monkeypatch):
        from know_ops_mcp.setup.config import Config

        replacement = MemoryStorage()

        class _StubConfig:
            def to_storage_backend(self):
                return replacement

        monkeypatch.setattr(Config, "load", classmethod(lambda cls: _StubConfig()))
        server.bootstrap()
        assert storage._backend is replacement
