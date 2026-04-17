"""cursor-memo MCP server."""

from __future__ import annotations

import json

from fastmcp import FastMCP
from pydantic import ValidationError

from cursor_memo import knowledge_ops

mcp = FastMCP(
    "cursor-memo",
    instructions=(
        "You are connected to cursor-memo, a shared knowledge store. "
        "Use these tools to search, read, write, list, and delete notes. "
        "Each note is identified by a unique_name (lowercase, hyphens, digits) "
        "agreed upon with the user."
    ),
)


def _format_validation_error(exc: ValidationError) -> str:
    parts = [f"- {'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return "Validation failed:\n" + "\n".join(parts)


@mcp.tool
def search_notes(query: str, tags: list[str] | None = None, limit: int = 10) -> str:
    """Search stored notes by keyword and optional tag filter.

    Match target: unique_name, title, description, content (case-insensitive).
    An empty query matches every note.

    Args:
        query: Search keyword.
        tags: Optional list of tags to filter results.
        limit: Maximum number of results to return (default 10).

    Returns:
        JSON list of note summaries (unique_name, type, title, description, tags).
    """
    results = knowledge_ops.search_notes(query, tags=tags, limit=limit)
    if not results:
        return "No notes found matching the query."
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool
def read_note(unique_name: str) -> str:
    """Read a specific note by its unique_name.

    Args:
        unique_name: The unique identifier of the note (e.g. 'python-async-patterns').

    Returns:
        Full note content including frontmatter, or an error message if not found.
    """
    note = knowledge_ops.read_note(unique_name)
    if note is None:
        return f"Note '{unique_name}' not found."
    return note.model_dump_json(indent=2)


@mcp.tool
def write_note(
    unique_name: str,
    title: str,
    description: str,
    content: str,
    tags: list[str] | None = None,
    type: str = "general",
) -> str:
    """Create or update a note.

    Args:
        unique_name: Unique identifier. Lowercase letters, digits, and hyphens only
            (e.g. 'python-async-patterns').
        title: Human-readable title shown when reading the note.
        description: One-line summary explaining what this note is about. Used by
            LLMs to decide whether this note is relevant before reading the full body.
        content: Markdown body of the note.
        tags: Optional list of tags for categorization.
        type: Note type discriminator (default 'general').

    Returns:
        JSON of the saved note, or a validation error message.
    """
    try:
        note = knowledge_ops.write_note(
            unique_name=unique_name,
            title=title,
            description=description,
            content=content,
            tags=tags,
            type=type,
        )
    except ValidationError as exc:
        return _format_validation_error(exc)
    return note.model_dump_json(indent=2)


@mcp.tool
def list_notes(tag: str | None = None) -> str:
    """List all stored notes, optionally filtered by a tag.

    Args:
        tag: Optional tag to filter the list.

    Returns:
        JSON list of note summaries.
    """
    results = knowledge_ops.list_notes(tag=tag)
    if not results:
        return "No notes found."
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool
def delete_note(unique_name: str) -> str:
    """Delete a note by its unique_name.

    Args:
        unique_name: The unique identifier of the note to delete.

    Returns:
        Confirmation or error message.
    """
    deleted = knowledge_ops.delete_note(unique_name)
    if deleted:
        return f"Note '{unique_name}' deleted."
    return f"Note '{unique_name}' not found."


def main():
    mcp.run()
