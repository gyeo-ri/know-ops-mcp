import pytest
from pydantic import ValidationError

from know_ops_mcp.knowledge.base import BaseKnowledge, for_type, register
from know_ops_mcp.knowledge.general import GeneralKnowledge


def _entry(**overrides) -> GeneralKnowledge:
    base = dict(
        knowledge_key="sample-entry",
        title="Sample",
        description="Sample entry.",
        created="2026-04-15",
        updated="2026-04-15",
        content="body",
    )
    base.update(overrides)
    return GeneralKnowledge(**base)


def test_for_type_returns_general():
    assert for_type("general") is GeneralKnowledge


def test_for_type_unknown_raises():
    with pytest.raises(ValueError, match="Unknown knowledge type"):
        for_type("does-not-exist")


def test_register_rejects_class_without_typed_default():
    class Bad(BaseKnowledge):
        type: str = ""

    with pytest.raises(ValueError, match="non-empty string default"):
        register(Bad)


def test_knowledge_key_pattern_enforced():
    with pytest.raises(ValidationError):
        _entry(knowledge_key="Has Spaces")
    with pytest.raises(ValidationError):
        _entry(knowledge_key="Mixed_Case")


def test_knowledge_key_allows_slashes():
    e = _entry(knowledge_key="project/topic")
    assert e.knowledge_key == "project/topic"
    e2 = _entry(knowledge_key="a/b/c")
    assert e2.knowledge_key == "a/b/c"


@pytest.mark.parametrize("bad_key", ["/leading", "trailing/", "a//b", "/", "a/b/"])
def test_knowledge_key_rejects_malformed_slashes(bad_key):
    with pytest.raises(ValidationError):
        _entry(knowledge_key=bad_key)


def test_serialize_deserialize_round_trip_via_base():
    original = _entry(tags=["a", "b"])
    text = original.serialize()
    restored = BaseKnowledge.deserialize(text)
    assert isinstance(restored, GeneralKnowledge)
    assert restored.model_dump() == original.model_dump()


def test_summary_excludes_dates_and_content():
    entry = _entry(tags=["x"])
    summary = entry.summary()
    assert summary == {
        "knowledge_key": "sample-entry",
        "type": "general",
        "title": "Sample",
        "description": "Sample entry.",
        "tags": ["x"],
    }
