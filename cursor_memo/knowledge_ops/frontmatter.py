"""Pure serialization between metadata dict + content string and markdown."""

from __future__ import annotations

import frontmatter


def dumps(metadata: dict, content: str) -> str:
    return frontmatter.dumps(frontmatter.Post(content, **metadata))


def loads(md: str) -> tuple[dict, str]:
    post = frontmatter.loads(md)
    return dict(post.metadata), post.content
