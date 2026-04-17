import pytest
from pydantic import ValidationError

from know_ops_mcp.knowledge.base import BaseKnowledge, for_type, register
from know_ops_mcp.knowledge.general import GeneralKnowledge


def _entry(**overrides) -> GeneralKnowledge:
    base = dict(
        unique_name="sample-entry",
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


def test_unique_name_pattern_enforced():
    with pytest.raises(ValidationError):
        _entry(unique_name="Has Spaces")
    with pytest.raises(ValidationError):
        _entry(unique_name="Mixed_Case")


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
        "unique_name": "sample-entry",
        "type": "general",
        "title": "Sample",
        "description": "Sample entry.",
        "tags": ["x"],
    }
