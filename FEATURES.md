# Features

구현 완료된 기능을 기록합니다.

## MCP Interface

FastMCP 3.2 기반 stdio MCP 서버. `cursor-memo` 명령으로 실행.

- 진입점: `cursor_memo/server.py` → `pyproject.toml`의 `[project.scripts]`로 CLI 등록

### MCP Tools

| Tool | 파라미터 | 기능 |
| --- | --- | --- |
| `search_notes` | `query`, `tags?`, `limit?` | unique_name + title + description + content 대상 키워드 검색, 태그 필터 |
| `read_note` | `unique_name` | unique_name으로 노트 전문 조회 |
| `write_note` | `unique_name`, `title`, `description`, `content`, `tags?`, `type?` | 노트 생성/수정 (Convention 검증) |
| `list_notes` | `tag?` | 노트 목록 조회 (태그 필터) |
| `delete_note` | `unique_name` | 노트 삭제 |

### 현재 상태

- 실제 GitHub Storage 연동은 미구현 (인메모리 stub 사용 중)

## Knowledge Ops

Pydantic 기반 Note 모델 + CRUD/검색.

### 구조

| 모듈 | 역할 |
| --- | --- |
| `cursor_memo/knowledge_ops/__init__.py` | CRUD + 검색 (`search_notes`, `read_note`, `write_note`, `list_notes`, `delete_note`) |
| `cursor_memo/knowledge_ops/note.py` | Pydantic `Note` 모델 (검증 + `from_markdown`/`to_markdown`) |
| `cursor_memo/knowledge_ops/frontmatter.py` | 순수 직렬화 유틸 (`dumps`, `loads`) |

### Note 스키마

| 필드 | 검증 | 비고 |
| --- | --- | --- |
| `unique_name` | `^[a-z0-9-]+$` | GitHub 파일명 안전 + 식별자 일관성 |
| `type` | (자유) | 기본값 `'general'`. 향후 타입별 모델 분리 예정 |
| `title` | min_length=1 | 사람이 읽는 제목 |
| `description` | min_length=1 | unique_name이 무엇에 관한지 한 줄 요약. 검색 대상 포함 |
| `tags` | (자유) | 분류 태그 |
| `created` / `updated` | auto | 생성 시 today, 수정 시 `updated`만 갱신, `created` 보존 |
| `content` | - | 마크다운 본문 |

### Frontmatter 예시

```yaml
---
unique_name: python-async-patterns
type: general
title: Python 비동기 패턴 정리
description: asyncio, TaskGroup 등 Python 비동기 처리 패턴 사용 사례 모음
tags: [python, async]
created: '2026-04-17'
updated: '2026-04-17'
---
```

### 검증 동작

- Convention 위반 시 `pydantic.ValidationError` → `server.py`에서 사용자 친화 메시지로 변환
- 예: `unique_name: String should match pattern '^[a-z0-9-]+$'`

## Storage (In-Memory Stub)

`cursor_memo/storage/memory.py` — dict 기반 인메모리 저장소. GitHub Storage 구현 전 개발/테스트용.
