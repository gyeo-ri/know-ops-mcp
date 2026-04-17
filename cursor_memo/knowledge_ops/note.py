"""Note domain model with self-validation and markdown (de)serialization."""

from __future__ import annotations

from pydantic import BaseModel, Field

from cursor_memo.knowledge_ops import frontmatter as fm


class Note(BaseModel):
    unique_name: str = Field(pattern=r"^[a-z0-9-]+$")
    type: str = "general"
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    tags: list[str] = []
    created: str
    updated: str
    content: str

    @classmethod
    def from_markdown(cls, md: str) -> "Note":
        meta, content = fm.loads(md)
        return cls(**meta, content=content)

    def to_markdown(self) -> str:
        meta = self.model_dump(exclude={"content"})
        return fm.dumps(meta, self.content)
