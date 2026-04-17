"""BaseKnowledge — common fields, serialization, and type dispatch registry."""

from __future__ import annotations

from pydantic import BaseModel, Field

from know_ops_mcp.know_ops.knowledge import serializer


_SUMMARY_FIELDS = {"unique_name", "type", "title", "description", "tags"}

_REGISTRY: dict[str, type["BaseKnowledge"]] = {}


class BaseKnowledge(BaseModel):
    unique_name: str = Field(pattern=r"^[a-z0-9-]+$")
    type: str
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    tags: list[str] = []
    created: str
    updated: str
    content: str

    @classmethod
    def deserialize(cls, text: str) -> "BaseKnowledge":
        meta, content = serializer.deserialize(text)
        type_ = meta.get("type", "general")
        return for_type(type_)(**meta, content=content)

    def serialize(self) -> str:
        meta = self.model_dump(exclude={"content"})
        return serializer.serialize(meta, self.content)

    def summary(self) -> dict:
        return self.model_dump(include=_SUMMARY_FIELDS)


def register(cls: type[BaseKnowledge]) -> type[BaseKnowledge]:
    type_value = cls.model_fields["type"].default
    if not isinstance(type_value, str) or not type_value:
        raise ValueError(
            f"{cls.__name__}: 'type' field must have a non-empty string default"
        )
    _REGISTRY[type_value] = cls
    return cls


def for_type(type_: str) -> type[BaseKnowledge]:
    if type_ not in _REGISTRY:
        raise ValueError(
            f"Unknown knowledge type: '{type_}'. Registered: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[type_]
