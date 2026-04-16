"""Knowledge operations stub. Returns hardcoded dummy data."""

from __future__ import annotations

DUMMY_NOTES = {
    "python-async-patterns": {
        "unique_name": "python-async-patterns",
        "title": "Python 비동기 패턴 정리",
        "tags": ["python", "async"],
        "created": "2026-04-15",
        "updated": "2026-04-15",
        "content": (
            "# Python 비동기 패턴 정리\n\n"
            "- `asyncio.gather`로 병렬 실행\n"
            "- `async for`로 비동기 이터레이션\n"
            "- `TaskGroup`으로 구조적 동시성\n"
        ),
    },
    "docker-troubleshooting": {
        "unique_name": "docker-troubleshooting",
        "title": "Docker 트러블슈팅 메모",
        "tags": ["docker", "devops"],
        "created": "2026-04-10",
        "updated": "2026-04-14",
        "content": (
            "# Docker 트러블슈팅 메모\n\n"
            "- 포트 충돌: `lsof -i :포트번호`로 확인\n"
            "- 볼륨 마운트 안 될 때: 경로에 공백 확인\n"
        ),
    },
}


def search_notes(
    query: str, tags: list[str] | None = None, limit: int = 10
) -> list[dict]:
    results = []
    for note in DUMMY_NOTES.values():
        if tags and not set(tags) & set(note["tags"]):
            continue
        if query.lower() in note["title"].lower() or query.lower() in note["content"].lower():
            results.append({
                "unique_name": note["unique_name"],
                "title": note["title"],
                "tags": note["tags"],
            })
    return results[:limit]


def read_note(unique_name: str) -> dict | None:
    return DUMMY_NOTES.get(unique_name)


def write_note(
    unique_name: str, title: str, content: str, tags: list[str] | None = None
) -> dict:
    DUMMY_NOTES[unique_name] = {
        "unique_name": unique_name,
        "title": title,
        "tags": tags or [],
        "created": "2026-04-16",
        "updated": "2026-04-16",
        "content": content,
    }
    return DUMMY_NOTES[unique_name]


def list_notes(tag: str | None = None) -> list[dict]:
    results = []
    for note in DUMMY_NOTES.values():
        if tag and tag not in note["tags"]:
            continue
        results.append({
            "unique_name": note["unique_name"],
            "title": note["title"],
            "tags": note["tags"],
        })
    return results


def delete_note(unique_name: str) -> bool:
    return DUMMY_NOTES.pop(unique_name, None) is not None
