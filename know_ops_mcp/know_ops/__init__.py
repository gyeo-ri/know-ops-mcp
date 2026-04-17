"""know_ops — knowledge management application layer.

`KnowOps` orchestrates the `knowledge` domain and `storage` infrastructure
into CRUD/search use cases.
"""

from __future__ import annotations

from datetime import date

from know_ops_mcp.know_ops.knowledge import BaseKnowledge, for_type
from know_ops_mcp.know_ops.storage import StorageService, storage as _default_storage


class KnowOps:
    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    def search(
        self, query: str, tags: list[str] | None = None, limit: int = 10
    ) -> list[dict]:
        results = []
        q = query.lower()
        for text in self._storage.list_all().values():
            knowledge = BaseKnowledge.deserialize(text)
            if tags and not set(tags) & set(knowledge.tags):
                continue
            haystack = " ".join([
                knowledge.unique_name, knowledge.title, knowledge.description, knowledge.content
            ]).lower()
            if q in haystack:
                results.append(knowledge.summary())
        return results[:limit]

    def read(self, unique_name: str) -> BaseKnowledge | None:
        text = self._storage.read(unique_name)
        if text is None:
            return None
        return BaseKnowledge.deserialize(text)

    def write(
        self,
        unique_name: str,
        title: str,
        description: str,
        content: str,
        tags: list[str] | None = None,
        type: str = "general",
    ) -> BaseKnowledge:
        knowledge_cls = for_type(type)
        today = date.today().isoformat()
        existing = self._storage.read(unique_name)
        created = (
            BaseKnowledge.deserialize(existing).created if existing else today
        )
        knowledge = knowledge_cls(
            unique_name=unique_name,
            type=type,
            title=title,
            description=description,
            tags=tags or [],
            created=created,
            updated=today,
            content=content,
        )
        self._storage.write(unique_name, knowledge.serialize())
        return knowledge

    def list_all(self, tag: str | None = None) -> list[dict]:
        results = []
        for text in self._storage.list_all().values():
            knowledge = BaseKnowledge.deserialize(text)
            if tag and tag not in knowledge.tags:
                continue
            results.append(knowledge.summary())
        return results

    def delete(self, unique_name: str) -> bool:
        return self._storage.delete(unique_name)


know_ops = KnowOps(_default_storage)


__all__ = ["KnowOps", "know_ops"]
