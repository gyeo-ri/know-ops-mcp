"""cursor-memo MCP server."""

from __future__ import annotations

import json

from fastmcp import FastMCP

from cursor_memo import ops

mcp = FastMCP(
    "cursor-memo",
    instructions=(
        "You are connected to cursor-memo, a shared knowledge store. "
        "Use these tools to search, read, write, list, and delete notes. "
        "Each note is identified by a unique_name agreed upon with the user."
    ),
)


@mcp.tool
def search_notes(query: str, tags: list[str] | None = None, limit: int = 10) -> str:
    """Search stored knowledge/context by keyword and optional tag filter.

    Args:
        query: Search keyword to match against note titles and content.
        tags: Optional list of tags to filter results.
        limit: Maximum number of results to return (default 10).

    Returns:
        JSON list of matching notes with unique_name, title, and tags.
    """
    results = ops.search_notes(query, tags=tags, limit=limit)
    if not results:
        return "No notes found matching the query."
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool
def read_note(unique_name: str) -> str:
    """Read a specific note by its unique_name.

    Args:
        unique_name: The unique identifier of the note (e.g. 'python-async-patterns').

    Returns:
        The full note content including frontmatter metadata, or an error message if not found.
    """
    note = ops.read_note(unique_name)
    if note is None:
        return f"Note '{unique_name}' not found."
    return json.dumps(note, ensure_ascii=False, indent=2)


@mcp.tool
def write_note(
    unique_name: str, title: str, content: str, tags: list[str] | None = None
) -> str:
    """Create or update a note.

    Args:
        unique_name: Unique identifier for the note (lowercase, hyphens, e.g. 'python-async-patterns').
        title: Human-readable title.
        content: Markdown body of the note.
        tags: Optional list of tags for categorization.

    Returns:
        Confirmation with the saved note metadata.
    """
    note = ops.write_note(unique_name, title, content, tags=tags)
    return json.dumps(note, ensure_ascii=False, indent=2)


@mcp.tool
def list_notes(tag: str | None = None) -> str:
    """List all stored notes, optionally filtered by a tag.

    Args:
        tag: Optional tag to filter the list.

    Returns:
        JSON list of notes with unique_name, title, and tags.
    """
    results = ops.list_notes(tag=tag)
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
    deleted = ops.delete_note(unique_name)
    if deleted:
        return f"Note '{unique_name}' deleted."
    return f"Note '{unique_name}' not found."


def main():
    mcp.run()
