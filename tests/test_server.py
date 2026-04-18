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


def _seed(knowledge_key: str = "alpha", **overrides) -> None:
    payload = dict(
        knowledge_key=knowledge_key,
        title="T",
        description="D",
        body="C",
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
        assert parsed[0]["knowledge_key"] == "alpha"
        assert "content" not in parsed[0]


class TestReadTool:
    def test_missing_returns_message(self):
        assert server.read_knowledge("ghost") == "Knowledge 'ghost' not found."

    def test_existing_returns_full_json(self):
        _seed("alpha", body="body")
        parsed = json.loads(server.read_knowledge("alpha"))
        assert parsed["knowledge_key"] == "alpha"
        assert parsed["content"] == "body"


class TestWriteTool:
    def test_success_returns_full_json(self):
        result = server.write_knowledge(
            knowledge_key="alpha", title="T", description="D", body="C"
        )
        parsed = json.loads(result)
        assert parsed["knowledge_key"] == "alpha"
        assert parsed["type"] == "general"

    def test_invalid_knowledge_key_returns_validation_message(self):
        result = server.write_knowledge(
            knowledge_key="Bad Name", title="T", description="D", body="C"
        )
        assert result.startswith("Validation failed:")
        assert "knowledge_key" in result

    def test_hierarchical_key_round_trip(self):
        result = server.write_knowledge(
            knowledge_key="proj/topic", title="T", description="D", body="C"
        )
        parsed = json.loads(result)
        assert parsed["knowledge_key"] == "proj/topic"
        read_result = json.loads(server.read_knowledge("proj/topic"))
        assert read_result["content"] == "C"

    def test_unknown_type_returns_error_message(self):
        result = server.write_knowledge(
            knowledge_key="alpha",
            title="T",
            description="D",
            body="C",
            type="nope",
        )
        assert result.startswith("Error:")
        assert "Unknown knowledge type" in result

    def test_body_path_reads_file(self, tmp_path):
        md = tmp_path / "note.md"
        md.write_text("body from file", encoding="utf-8")
        result = server.write_knowledge(
            knowledge_key="alpha", title="T", description="D",
            body_path=str(md),
        )
        parsed = json.loads(result)
        assert parsed["content"] == "body from file"

    def test_body_and_body_path_both_given_returns_error(self, tmp_path):
        md = tmp_path / "note.md"
        md.write_text("x", encoding="utf-8")
        result = server.write_knowledge(
            knowledge_key="alpha", title="T", description="D",
            body="inline", body_path=str(md),
        )
        assert "not both" in result

    def test_body_path_missing_file_returns_error(self):
        result = server.write_knowledge(
            knowledge_key="alpha", title="T", description="D",
            body_path="/tmp/nonexistent-9999.md",
        )
        assert "File not found" in result

    def test_neither_body_nor_path_returns_error(self):
        result = server.write_knowledge(
            knowledge_key="alpha", title="T", description="D",
        )
        assert "must be provided" in result


class TestListTool:
    def test_empty_returns_message(self):
        assert server.list_knowledge() == "No knowledge entries found."

    def test_returns_summaries_as_json(self):
        _seed("a")
        _seed("b")
        parsed = json.loads(server.list_knowledge())
        assert {p["knowledge_key"] for p in parsed} == {"a", "b"}

    def test_tag_filter(self):
        _seed("a", tags=["x"])
        _seed("b", tags=["y"])
        parsed = json.loads(server.list_knowledge(tag="x"))
        assert [p["knowledge_key"] for p in parsed] == ["a"]

    def test_prefix_filter(self):
        _seed("proj/a")
        _seed("proj/b")
        _seed("other")
        parsed = json.loads(server.list_knowledge(prefix="proj/"))
        assert {p["knowledge_key"] for p in parsed} == {"proj/a", "proj/b"}


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
