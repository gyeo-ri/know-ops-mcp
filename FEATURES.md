---
purpose: 구현 완료된 기능의 카탈로그 (코드 → 의도 매핑)
audience: [humans, agents]
update_when: 기능 추가/제거/시그니처 변경 시
---

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
| `refresh_knowledge_cache` | `unique_name?` | 로컬 캐시 무효화 (단건 / 전체). Cached backend 전용; 비캐시 backend에선 no-op |

### 현재 상태

- `Config.to_storage_backend()`가 storage type에 따라 적절한 backend 인스턴스를 반환:
  - `local` → `LocalDirectoryStorage(path)`
  - `github` → `CachedStorage(GitHubStorage(...), cache_dir=default_cache_dir())`
- config 부재 시 `MemoryStorage` fallback + stderr 경고

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
2. backend type 선택 (`local` / `github`)
3. backend별 추가 질문:
   - **local**: storage 경로 입력 (기본 `$XDG_DATA_HOME/know-ops-mcp`, 미설정 시 `~/.local/share/know-ops-mcp`) → `LocalDirectoryStorage` 인스턴스화로 검증
   - **github**: repo URL + token (token 비우면 `KNOW_OPS_MCP_GITHUB_TOKEN` env var 사용). branch/subdirectory는 기본값 (`main` / 루트). 변경 필요 시 `config.toml` 직접 편집
4. `~/.config/know-ops-mcp/config.toml`에 저장 (mode `0600`)
5. MCP 표준 등록 스니펫 출력 → 사용자가 자기 클라이언트의 설정 파일에 붙여넣음

### 책임 경계

- 이 도구는 **MCP 서버**다. 누가 호출하는지(Cursor/Claude/Continue/...) 알 필요 없음
- 클라이언트 설치/등록 확인은 각 클라이언트 책임
- 자동화 허용 범위: `~/.config/know-ops-mcp/` (자체 config), `~/.cache/know-ops-mcp/` (자체 캐시), 사용자가 명시한 storage 경로 / GitHub repo
- 외부 도구의 설정 파일은 읽지도 쓰지도 않음

### 구조

| 모듈 | 역할 |
| --- | --- |
| `know_ops_mcp/setup/cli.py` | typer app — `serve` / `setup` |
| `know_ops_mcp/setup/wizard.py` | 대화형 흐름 (questionary) — backend 선택 → 분기 prompt → 진단 / 스니펫 출력 |
| `know_ops_mcp/setup/config.py` | `Config` Pydantic + discriminated union (`LocalStorageConfig` / `GitHubStorageConfig`) + TOML load/save (XDG, `chmod 0600`) + `to_storage_backend()` |

### 설정 파일

위치: `~/.config/know-ops-mcp/config.toml` (XDG_CONFIG_HOME 존중). 권한: `0600`.

```toml
[storage]
type = "local"
path = "~/.local/share/know-ops-mcp"
```

또는

```toml
[storage]
type = "github"
repo_url = "https://github.com/yourname/your-knowledge-repo"
branch = "main"
subdirectory = ""
token = "ghp_xxxxxxxxxxxxxxxx"
```

사람이 직접 편집 가능. 서버 재시작 시 반영. 스키마 위반은 Pydantic 에러로 안내.

#### Token 우선순위 (GitHub backend 한정)

1. `KNOW_OPS_MCP_GITHUB_TOKEN` 환경변수 (set 되어 있으면 무조건 우선)
2. `config.toml`의 `storage.token` 값
3. 둘 다 없으면 `RuntimeError` (명확한 안내 메시지)

### MCP 등록 스니펫

마법사가 출력하는 표준 형식 (Cursor / Claude Desktop / Continue 등 공통). `command`/`args`는 wizard가 자기 설치 출처(`importlib.metadata` PEP 610 `direct_url.json`)를 보고 자동 결정.

| 설치 출처 | 출력 args |
| --- | --- |
| PyPI (정식 배포) | `["know-ops-mcp"]` |
| git URL (`uvx --from git+...`) | `["--from", "git+<url>@<commit>", "know-ops-mcp"]` |
| 로컬 체크아웃 (`uvx --from /path` 또는 `uv tool install --editable`) | `["--from", "<absolute path>", "know-ops-mcp"]` |

PyPI 배포 후의 표준형:

```json
{
  "mcpServers": {
    "know-ops-mcp": {
      "command": "uvx",
      "args": ["know-ops-mcp"]
    }
  }
}
```

`uvx`가 PATH에 없으면 마법사가 install 안내(`https://docs.astral.sh/uv/...`)를 출력. 자동 설치는 안 함(외부 side-effect 정책).

## know_ops (애플리케이션 레이어)

CRUD/검색 유스케이스를 제공하는 단일 모듈. 도메인(`knowledge`)과 인프라(`storage`)는 형제 패키지로 분리.

### 구조

| 모듈 | 역할 |
| --- | --- |
| `know_ops_mcp/know_ops.py` | `KnowOps` 서비스 클래스 (`search/read/write/list_all/delete/refresh`) + 기본 싱글턴 `know_ops` |
| `know_ops_mcp/knowledge/__init__.py` | `BaseKnowledge`, `GeneralKnowledge`, `register`, `for_type` re-export |
| `know_ops_mcp/knowledge/base.py` | `BaseKnowledge` (공통 필드 + serialize/deserialize/summary + 타입 dispatch 레지스트리) |
| `know_ops_mcp/knowledge/general.py` | `GeneralKnowledge(BaseKnowledge)` (type="general") |
| `know_ops_mcp/knowledge/serializer.py` | 직렬화 유틸 (`serialize`, `deserialize`). 현재 구현: YAML frontmatter + md |
| `know_ops_mcp/storage/...` | 인프라 (아래 Storage 섹션 참조) |

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

ABC 기반 인터페이스 + 구현체 분리. `StorageService`가 단일 진입점이고, MCP 서버 부트스트랩에서 user config에 따라 backend를 교체.

### 클래스 계층

```
BaseStorage (ABC)                        read/write/delete/list_all
├── InternalStorage (marker)             외부 의존 없음
│   ├── MemoryStorage                    dict 기반, 테스트/단위 검증용
│   └── LocalDirectoryStorage            로컬 디렉토리 1파일/entry (.md)
├── ExternalStorage (ABC)                + list_versions: name → opaque version
│   └── GitHubStorage                    GitHub REST Contents API + Trees API
└── CachedStorage                        ExternalStorage 데코레이터 (cache-on-read)
```

### 구조

| 모듈 | 역할 |
| --- | --- |
| `know_ops_mcp/storage/base.py` | `BaseStorage` ABC (`read`, `write`, `delete`, `list_all`) |
| `know_ops_mcp/storage/__init__.py` | `StorageService` (backend 위임 + `configure` + `refresh`) + 기본 싱글턴 `storage` + 모든 backend re-export |
| `know_ops_mcp/storage/disk.py` | 디스크 R/W 헬퍼 (`ensure`/`read`/`write`/`delete`/`list_all`/`clear`). `LocalDirectoryStorage`와 `CachedStorage` 공유 |
| `know_ops_mcp/storage/cache.py` | `CachedStorage` 데코레이터 + `default_cache_dir()` (XDG_CACHE_HOME 존중) |
| `know_ops_mcp/storage/backends/internal/__init__.py` | `InternalStorage` marker (외부 의존 X 그룹) |
| `know_ops_mcp/storage/backends/internal/memory.py` | `MemoryStorage(InternalStorage)` |
| `know_ops_mcp/storage/backends/internal/local.py` | `LocalDirectoryStorage(InternalStorage)` — `disk.py` 헬퍼 사용 |
| `know_ops_mcp/storage/backends/external/__init__.py` | `ExternalStorage` ABC (+ abstract `list_versions`) |
| `know_ops_mcp/storage/backends/external/github.py` | `GitHubStorage` (httpx 기반 REST API, Trees listing, rate limit 1회 재시도) |

### LocalDirectoryStorage

- `LocalDirectoryStorage(path)` — `~` 확장 + 절대경로 정규화, 부재 시 디렉토리 자동 생성
- 파일 매핑: `unique_name` ↔ `<path>/<unique_name>.md`
- `default_data_dir()` — wizard가 default로 제안. `$XDG_DATA_HOME/know-ops-mcp`, env 부재 시 `~/.local/share/know-ops-mcp` (M17)
- 사용 시나리오: 단일 기기 prod

### GitHubStorage

- `GitHubStorage(repo_url, token, *, subdirectory="", branch="main")`
- Read/Write/Delete: GitHub REST Contents API (`GET/PUT/DELETE /repos/{owner}/{repo}/contents/<path>`)
- Listing: Git Trees API (`GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=true`). truncated 응답 시 `RuntimeError` raise (silent 누락 방지)
- 인증: PAT (`Authorization: Bearer <token>`)
- Rate limit: 429 또는 403 + `x-ratelimit-remaining=0` 시 `Retry-After` / `X-RateLimit-Reset` 따라 sleep, 1회 재시도 (60초 cap)
- `parse_repo_url(url) -> (owner, repo)` 헬퍼 — `https://github.com/owner/repo[.git]` 형식만 허용
- 단독 사용 가능하지만 매 호출 API 트래픽 발생. 일반적으로 `CachedStorage`로 wrapping

### CachedStorage

- `CachedStorage(backend: ExternalStorage, cache_dir)` — 어떤 `ExternalStorage`든 wrapping
- 캐시 위치: `cache_dir` 인자. 기본값은 `default_cache_dir()` = `$XDG_CACHE_HOME/know-ops-mcp` 또는 `~/.cache/know-ops-mcp`
- 캐시 구조: `<cache_dir>/<unique_name>.md` 파일만 저장 (메타파일 X)
- TTL: 무한. 갱신은 명시적 `refresh(name=None)` 호출만

#### 정책 (cache-on-read)

| 연산 | 동작 |
| --- | --- |
| `read(name)` | 캐시 hit → 그대로. miss → backend → 캐시 저장 |
| `list_all()` | `backend.list_versions()`로 이름 얻고 각 read() → 자연스럽게 캐시 활용 |
| `write(name, content)` | backend.write 후 캐시 즉시 갱신 (write-through, backend 실패 시 캐시 미오염) |
| `delete(name)` | backend.delete 후 캐시 evict |
| `refresh(name=None)` | 캐시 파일 제거. 다음 read 때 fetch |

설계 근거 + 검토한 대안: [HISTORY.md M16](HISTORY.md).

### 호출 패턴

```python
from know_ops_mcp.storage import storage, LocalDirectoryStorage

storage.configure(LocalDirectoryStorage("~/Documents/know-ops-mcp"))
storage.write("foo", "...")
```

또는

```python
from know_ops_mcp.storage import (
    storage, GitHubStorage, CachedStorage, default_cache_dir,
)

backend = CachedStorage(
    GitHubStorage("https://github.com/me/notes", token="ghp_xxx"),
    cache_dir=default_cache_dir(),
)
storage.configure(backend)
```

### 현재 상태

- 구현체: `MemoryStorage`, `LocalDirectoryStorage`, `GitHubStorage`, `CachedStorage`
- 기본 싱글턴 `storage = StorageService(MemoryStorage())` — `bootstrap()`이 user config에 따라 `configure()` 호출
- `StorageService.refresh()`는 backend가 `refresh` 메서드를 가질 때만 위임 (Local/Memory에선 silent no-op)
