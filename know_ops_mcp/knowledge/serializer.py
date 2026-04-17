"""Serialize Knowledge metadata + content to/from a self-describing text representation.

Current implementation: YAML frontmatter + markdown body. Internal detail —
callers depend only on the (metadata dict, content string) <-> str contract.
"""

from __future__ import annotations

import frontmatter as _fm


def serialize(metadata: dict, content: str) -> str:
    return _fm.dumps(_fm.Post(content, **metadata))


def deserialize(text: str) -> tuple[dict, str]:
    post = _fm.loads(text)
    return dict(post.metadata), post.content
