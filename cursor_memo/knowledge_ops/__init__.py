"""Knowledge Ops — CRUD and search over Note objects."""

from __future__ import annotations

from datetime import date

from cursor_memo.knowledge_ops.note import Note
from cursor_memo.storage import delete as storage_delete
from cursor_memo.storage import list_all as storage_list_all
from cursor_memo.storage import read as storage_read
from cursor_memo.storage import write as storage_write


def _summary(note: Note) -> dict:
    return {
        "unique_name": note.unique_name,
        "type": note.type,
        "title": note.title,
        "description": note.description,
        "tags": note.tags,
    }


def search_notes(
    query: str, tags: list[str] | None = None, limit: int = 10
) -> list[dict]:
    results = []
    q = query.lower()
    for md_string in storage_list_all().values():
        note = Note.from_markdown(md_string)
        if tags and not set(tags) & set(note.tags):
            continue
        haystack = " ".join([
            note.unique_name, note.title, note.description, note.content
        ]).lower()
        if q in haystack:
            results.append(_summary(note))
    return results[:limit]


def read_note(unique_name: str) -> Note | None:
    md_string = storage_read(unique_name)
    if md_string is None:
        return None
    return Note.from_markdown(md_string)


def write_note(
    unique_name: str,
    title: str,
    description: str,
    content: str,
    tags: list[str] | None = None,
    type: str = "general",
) -> Note:
    today = date.today().isoformat()
    existing_md = storage_read(unique_name)
    created = (
        Note.from_markdown(existing_md).created if existing_md else today
    )
    note = Note(
        unique_name=unique_name,
        type=type,
        title=title,
        description=description,
        tags=tags or [],
        created=created,
        updated=today,
        content=content,
    )
    storage_write(unique_name, note.to_markdown())
    return note


def list_notes(tag: str | None = None) -> list[dict]:
    results = []
    for md_string in storage_list_all().values():
        note = Note.from_markdown(md_string)
        if tag and tag not in note.tags:
            continue
        results.append(_summary(note))
    return results


def delete_note(unique_name: str) -> bool:
    return storage_delete(unique_name)
