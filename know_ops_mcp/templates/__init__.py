"""Knowledge-base writing conventions: a style guide + per-doc-type templates.

The style guide and templates are plain markdown shipped inside the package, so
they version with the server and are reusable across every project and
knowledge base. The MCP exposes them through the ``get_writing_guide`` tool, and
a condensed form is seeded into each store's README on setup.

Adding a doc type: drop a ``<doc-type>.md`` template next to this module and add
its name to ``DOC_TYPES``.
"""

from __future__ import annotations

from importlib import resources

# Canonical document types, in the order they're surfaced to the LLM.
DOC_TYPES: list[str] = [
    "overview",
    "architecture",
    "design-decisions",
    "history",
    "session",
    "roadmap",
    "todo",
    "runbook",
    "note",
]


def load_style_guide() -> str:
    """Return the full style guide markdown."""
    return (resources.files(__package__) / "style-guide.md").read_text(encoding="utf-8")


def load_template(doc_type: str) -> str | None:
    """Return the markdown template for ``doc_type``, or None if unknown."""
    if doc_type not in DOC_TYPES:
        return None
    return (resources.files(__package__) / f"{doc_type}.md").read_text(encoding="utf-8")


__all__ = ["DOC_TYPES", "load_style_guide", "load_template"]
