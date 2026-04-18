"""know-ops-mcp server."""

from __future__ import annotations

import json
import sys
from pathlib import Path

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
        "Each entry is identified by a knowledge_key (lowercase, hyphens, digits, "
        "and forward slashes for hierarchy like 'project/topic') agreed upon with the user."
    ),
)


def _format_validation_error(exc: ValidationError) -> str:
    parts = [f"- {'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return "Validation failed:\n" + "\n".join(parts)


@mcp.tool
def search_knowledge(query: str, tags: list[str] | None = None, limit: int = 10) -> str:
    """Search stored knowledge entries by keyword and optional tag filter.

    Match target: knowledge_key, title, description, content (case-insensitive).
    An empty query matches every entry.

    Args:
        query: Search keyword.
        tags: Optional list of tags to filter results.
        limit: Maximum number of results to return (default 10).

    Returns:
        JSON list of summaries (knowledge_key, type, title, description, tags).
    """
    results = know_ops.search(query, tags=tags, limit=limit)
    if not results:
        return "No knowledge entries found matching the query."
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool
def read_knowledge(knowledge_key: str) -> str:
    """Read a specific knowledge entry by its knowledge_key.

    Args:
        knowledge_key: The unique identifier of the entry (e.g. 'python-async-patterns').

    Returns:
        Full entry content including frontmatter, or an error message if not found.
    """
    knowledge = know_ops.read(knowledge_key)
    if knowledge is None:
        return f"Knowledge '{knowledge_key}' not found."
    return knowledge.model_dump_json(indent=2)


@mcp.tool
def write_knowledge(
    knowledge_key: str,
    title: str,
    description: str,
    body: str | None = None,
    body_path: str | None = None,
    tags: list[str] | None = None,
    type: str = "general",
) -> str:
    """Create or update a knowledge entry.

    Args:
        knowledge_key: Unique identifier. Lowercase letters, digits, hyphens, and
            forward slashes (e.g. 'python-async-patterns' or 'project/topic').
        title: Human-readable title shown when reading the entry.
        description: One-line summary explaining what this entry is about. Used by
            LLMs to decide whether this entry is relevant before reading the full body.
        body: Markdown body of the entry (plain string).
        body_path: Local file path to read the markdown body from. Use this
            instead of body when the body is large. Mutually exclusive with body.
        tags: Optional list of tags for categorization.
        type: Knowledge type discriminator (default 'general').

    Returns:
        JSON of the saved entry, or a validation error message.
    """
    if body and body_path:
        return "Error: Provide either 'body' or 'body_path', not both."
    if body_path:
        path = Path(body_path).expanduser()
        if not path.is_file():
            return f"Error: File not found: {body_path}"
        body = path.read_text(encoding="utf-8")
    if not body:
        return "Error: Either 'body' or 'body_path' must be provided."
    try:
        knowledge = know_ops.write(
            knowledge_key=knowledge_key,
            title=title,
            description=description,
            content=body,
            tags=tags,
            type=type,
        )
    except ValidationError as exc:
        return _format_validation_error(exc)
    except ValueError as exc:
        return f"Error: {exc}"
    return knowledge.model_dump_json(indent=2)


@mcp.tool
def list_knowledge(tag: str | None = None, prefix: str | None = None) -> str:
    """List all stored knowledge entries, optionally filtered by tag or key prefix.

    Args:
        tag: Optional tag to filter the list.
        prefix: Optional knowledge_key prefix to list entries under a specific
            path (e.g. 'know-ops-mcp/' lists all entries in that directory).

    Returns:
        JSON list of summaries.
    """
    results = know_ops.list_all(tag=tag, prefix=prefix)
    if not results:
        return "No knowledge entries found."
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool
def refresh_knowledge_cache(knowledge_key: str | None = None) -> str:
    """Refresh the local cache against the upstream storage.

    Use this after a knowledge entry has been modified on another device or
    directly in the upstream repository, so subsequent reads see the latest
    version. Has no effect when the backend does not use caching.

    Args:
        knowledge_key: If provided, refresh only this entry. Otherwise refresh
            the entire cache.

    Returns:
        Confirmation message.
    """
    know_ops.refresh(knowledge_key)
    if knowledge_key:
        return f"Cache refreshed for '{knowledge_key}'."
    return "Cache refreshed."


@mcp.tool
def delete_knowledge(knowledge_key: str) -> str:
    """Delete a knowledge entry by its knowledge_key.

    Args:
        knowledge_key: The unique identifier of the entry to delete.

    Returns:
        Confirmation or error message.
    """
    deleted = know_ops.delete(knowledge_key)
    if deleted:
        return f"Knowledge '{knowledge_key}' deleted."
    return f"Knowledge '{knowledge_key}' not found."


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
