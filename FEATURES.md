# Features

구현 완료된 기능을 기록합니다.

## MCP Interface

FastMCP 3.2 기반 stdio MCP 서버. CLI에서 `know-ops-mcp serve`(또는 인자 없이 `know-ops-mcp`)로 실행되며, MCP 클라이언트가 subprocess로 자동 launch.

- 진입점: `know_ops_mcp/setup/cli.py:app` → `pyproject.toml` `[project.scripts]`
- 시작 시 `know_ops_mcp.server.bootstrap()`이 user config을 로드해 storage 백엔드를 적용

### MCP Tools

| Tool | 파라미터 | 기능 |
| --- | --- | --- |
| `search_knowledge` | `query`, `tags?`, `limit?` | unique_name + title + description + content 대상 키워드 검색, 태그 필터 |
| `read_knowledge` | `unique_name` | unique_name으로 entry 전문 조회 |
| `write_knowledge` | `unique_name`, `title`, `description`, `content`, `tags?`, `type?` | entry 생성/수정 (Convention 검증) |
| `list_knowledge` | `tag?` | entry 목록 조회 (태그 필터) |
| `delete_knowledge` | `unique_name` | entry 삭제 |

### 현재 상태

- 사용자 config의 storage path를 읽어 `LocalDirectoryStorage`로 backend 구성. config 부재 시 `MemoryStorage` fallback + stderr 경고

## Setup CLI

클라이언트-무관 사용자 인터페이스. 어떤 LLM 클라이언트를 쓰든 동일한 절차.

### 명령

| 명령 | 동작 |
| --- | --- |
| `know-ops-mcp` | 인자 없으면 `serve`와 동일 (클라이언트가 호출하는 형태) |
| `know-ops-mcp serve` | MCP 서버 실행 (stdio) |
| `know-ops-mcp setup` | 대화형 마법사. 재실행 시 현재 config + 스니펫만 보기도 가능 |

### 마법사 흐름

1. 기존 config 있으면 표시 후 "수정하시겠습니까?" 확인
   - **No** → 현재 config + MCP 등록 스니펫 출력 후 종료 (read-only 진단 경로)
   - **Yes** → 다음 단계
2. storage 경로 입력 (기본 `~/Documents/know-ops-mcp`) → `LocalDirectoryStorage` 인스턴스화로 검증
3. `~/.config/know-ops-mcp/config.toml` 저장
4. MCP 표준 등록 스니펫 출력 → 사용자가 자기 클라이언트의 설정 파일에 붙여넣음

### 책임 경계

- 이 도구는 **MCP 서버**다. 누가 호출하는지(Cursor/Claude/Continue/...) 알 필요 없음
- 클라이언트 설치/등록 확인은 각 클라이언트 책임
- 자동화 허용 범위: `~/.config/know-ops-mcp/` (자체 config), 사용자가 명시한 storage 경로
- 외부 도구의 설정 파일은 읽지도 쓰지도 않음

### 구조

| 모듈 | 역할 |
| --- | --- |
| `know_ops_mcp/setup/cli.py` | typer app — `serve` / `setup` |
| `know_ops_mcp/setup/wizard.py` | 대화형 흐름 (questionary) — 경로 입력 / 진단 / 스니펫 출력 |
| `know_ops_mcp/setup/config.py` | `Config` Pydantic + TOML load/save (XDG) + `to_storage_backend()` |

### 설정 파일

위치: `~/.config/know-ops-mcp/config.toml` (XDG_CONFIG_HOME 존중)

```toml
[storage]
path = "~/Documents/know-ops-mcp"
```

사람이 직접 편집 가능. 서버 재시작 시 반영. 스키마 위반은 Pydantic 에러로 안내.

### MCP 등록 스니펫

마법사가 출력하는 표준 형식 (Cursor / Claude Desktop / Continue 등 공통):

```json
{
  "mcpServers": {
    "know-ops-mcp": {
      "command": "know-ops-mcp"
    }
  }
}
```

## know_ops (지식 관리 시스템)

애플리케이션 레이어. 도메인(`knowledge`)과 인프라(`storage`)를 안에 포함하고 CRUD/검색 유스케이스를 제공.

### 구조

| 모듈 | 역할 |
| --- | --- |
| `know_ops_mcp/know_ops/__init__.py` | `KnowOps` 서비스 클래스 (`search/read/write/list_all/delete`) + 기본 싱글턴 `know_ops` |
| `know_ops_mcp/know_ops/knowledge/__init__.py` | `BaseKnowledge`, `GeneralKnowledge`, `register`, `for_type` re-export |
| `know_ops_mcp/know_ops/knowledge/base.py` | `BaseKnowledge` (공통 필드 + serialize/deserialize/summary + 타입 dispatch 레지스트리) |
| `know_ops_mcp/know_ops/knowledge/general.py` | `GeneralKnowledge(BaseKnowledge)` (type="general") |
| `know_ops_mcp/know_ops/knowledge/serializer.py` | 직렬화 유틸 (`serialize`, `deserialize`). 현재 구현: YAML frontmatter + md |
| `know_ops_mcp/know_ops/storage/...` | 인프라 (아래 Storage 섹션 참조) |

### Knowledge 타입 시스템

```
BaseKnowledge (BaseModel)         공통 필드 + serialize/deserialize/summary
└── GeneralKnowledge              type: Literal["general"] = "general"
```

- 등록: `@register` 데코레이터 — 클래스의 `type` 필드 default 값으로 레지스트리 키 생성
- 조회: `for_type(type_str) -> type[BaseKnowledge]` (미등록 시 `ValueError`)
- 역직렬화: `BaseKnowledge.deserialize(text)`가 frontmatter의 `type`을 보고 적절한 서브클래스로 dispatch
- 새 타입 추가: `knowledge/<name>.py`에 `BaseKnowledge` 상속 + 추가 필드 정의 + `@register` + `knowledge/__init__.py`에 import 한 줄

### 스키마

| 필드 | 검증 | 비고 |
| --- | --- | --- |
| `unique_name` | `^[a-z0-9-]+$` | GitHub 파일명 안전 + 식별자 일관성 |
| `type` | (서브타입 강제) | 기본값 `'general'`. `Literal[...]`로 자기 값 강제 |
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

- Convention 위반: `pydantic.ValidationError` → `server.py`에서 사용자 친화 메시지로 변환
- 미등록 type: `ValueError` → `server.py`에서 `Error: Unknown knowledge type: ...` 형태로 반환

## Storage

ABC 기반 인터페이스 + 구현체 분리. 호출 측은 `know_ops.storage` 패키지의 모듈 함수를 사용 (default 인스턴스로 위임).

### 클래스 계층

```
BaseStorage (ABC)
└── InternalStorage (marker)              외부 의존 없음
    ├── MemoryStorage                     dict 기반, 테스트/단위 검증용
    └── LocalDirectoryStorage             로컬 디렉토리 1파일/entry (.md)
```

향후 `ExternalStorage` 계열(`GitHubStorage` 등, 캐시 옵션 내장)이 추가될 예정.

### 구조

| 모듈 | 역할 |
| --- | --- |
| `know_ops_mcp/know_ops/storage/base.py` | `BaseStorage` ABC (`read`, `write`, `delete`, `list_all`) |
| `know_ops_mcp/know_ops/storage/__init__.py` | `StorageService` (backend 위임 + `configure`) + 기본 싱글턴 `storage` |
| `know_ops_mcp/know_ops/storage/backends/internal/__init__.py` | `InternalStorage` marker (외부 의존 X 그룹) |
| `know_ops_mcp/know_ops/storage/backends/internal/memory.py` | `MemoryStorage(InternalStorage)` |
| `know_ops_mcp/know_ops/storage/backends/internal/local.py` | `LocalDirectoryStorage(InternalStorage)` |

### LocalDirectoryStorage

- `LocalDirectoryStorage(path)` — `~` 확장 + 절대경로 정규화, 부재 시 디렉토리 자동 생성
- 파일 매핑: `unique_name` ↔ `<path>/<unique_name>.md`
- 사용 시나리오: 단일 기기 prod, 또는 향후 `ExternalStorage`의 캐시 인자

### 호출 패턴

```python
from know_ops_mcp.know_ops.storage import storage, LocalDirectoryStorage

storage.configure(LocalDirectoryStorage("~/Documents/know-ops-mcp"))
storage.write("foo", "...")
```

향후 백엔드 교체도 `storage.configure(GitHubStorage(...))` 한 줄.

### 현재 상태

- 구현체: `MemoryStorage`, `LocalDirectoryStorage`
- 기본 싱글턴 `storage = StorageService(MemoryStorage())` (설정 기반 backend 선택은 미구현)
- ExternalStorage / GitHubStorage 미구현
