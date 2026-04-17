"""know-ops-mcp server."""

from __future__ import annotations

import json
import sys

from fastmcp import FastMCP
from pydantic import ValidationError

from know_ops_mcp.know_ops import know_ops
from know_ops_mcp.storage import storage
from know_ops_mcp.setup.config import Config

mcp = FastMCP(
    "know-ops-mcp",
    instructions=(
        "You are connected to know-ops-mcp, a shared knowledge store. "
        "Use these tools to search, read, write, list, and delete knowledge entries. "
        "Each entry is identified by a unique_name (lowercase, hyphens, digits) "
        "agreed upon with the user."
    ),
)


def _format_validation_error(exc: ValidationError) -> str:
    parts = [f"- {'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return "Validation failed:\n" + "\n".join(parts)


@mcp.tool
def search_knowledge(query: str, tags: list[str] | None = None, limit: int = 10) -> str:
    """Search stored knowledge entries by keyword and optional tag filter.

    Match target: unique_name, title, description, content (case-insensitive).
    An empty query matches every entry.

    Args:
        query: Search keyword.
        tags: Optional list of tags to filter results.
        limit: Maximum number of results to return (default 10).

    Returns:
        JSON list of summaries (unique_name, type, title, description, tags).
    """
    results = know_ops.search(query, tags=tags, limit=limit)
    if not results:
        return "No knowledge entries found matching the query."
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool
def read_knowledge(unique_name: str) -> str:
    """Read a specific knowledge entry by its unique_name.

    Args:
        unique_name: The unique identifier of the entry (e.g. 'python-async-patterns').

    Returns:
        Full entry content including frontmatter, or an error message if not found.
    """
    knowledge = know_ops.read(unique_name)
    if knowledge is None:
        return f"Knowledge '{unique_name}' not found."
    return knowledge.model_dump_json(indent=2)


@mcp.tool
def write_knowledge(
    unique_name: str,
    title: str,
    description: str,
    content: str,
    tags: list[str] | None = None,
    type: str = "general",
) -> str:
    """Create or update a knowledge entry.

    Args:
        unique_name: Unique identifier. Lowercase letters, digits, and hyphens only
            (e.g. 'python-async-patterns').
        title: Human-readable title shown when reading the entry.
        description: One-line summary explaining what this entry is about. Used by
            LLMs to decide whether this entry is relevant before reading the full body.
        content: Markdown body of the entry.
        tags: Optional list of tags for categorization.
        type: Knowledge type discriminator (default 'general').

    Returns:
        JSON of the saved entry, or a validation error message.
    """
    try:
        knowledge = know_ops.write(
            unique_name=unique_name,
            title=title,
            description=description,
            content=content,
            tags=tags,
            type=type,
        )
    except ValidationError as exc:
        return _format_validation_error(exc)
    except ValueError as exc:
        return f"Error: {exc}"
    return knowledge.model_dump_json(indent=2)


@mcp.tool
def list_knowledge(tag: str | None = None) -> str:
    """List all stored knowledge entries, optionally filtered by a tag.

    Args:
        tag: Optional tag to filter the list.

    Returns:
        JSON list of summaries.
    """
    results = know_ops.list_all(tag=tag)
    if not results:
        return "No knowledge entries found."
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool
def delete_knowledge(unique_name: str) -> str:
    """Delete a knowledge entry by its unique_name.

    Args:
        unique_name: The unique identifier of the entry to delete.

    Returns:
        Confirmation or error message.
    """
    deleted = know_ops.delete(unique_name)
    if deleted:
        return f"Knowledge '{unique_name}' deleted."
    return f"Knowledge '{unique_name}' not found."


def bootstrap() -> None:
    """Apply user config (if any) to the storage singleton."""
    config = Config.load()
    if config is None:
        print(
            "[know-ops-mcp] No config found. Using in-memory storage (data will be lost on exit).\n"
            "              Run `know-ops-mcp setup` to configure persistent storage.",
            file=sys.stderr,
        )
        return
    storage.configure(config.to_storage_backend())


def main():
    bootstrap()
    mcp.run()
