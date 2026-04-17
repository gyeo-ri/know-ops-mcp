---
purpose: 현재 구현된 아키텍처와 각 모듈의 책임/계약 (intent + impl)
audience: [humans, agents]
update_when: 모듈 추가·제거, 계약 변경, 정책 변경 시
---

# Architecture

설계 결정의 *근거*는 [`CHANGELOG.md`](CHANGELOG.md) (M번호). 본 문서는 *현재 상태*만 기술. 미해결 항목은 [`ROADMAP.md`](ROADMAP.md).

## 구성요소

| 레이어 | 위치 | 역할 |
| --- | --- | --- |
| Interface | `know_ops_mcp/server.py` | MCP tool 노출 (FastMCP + bootstrap) |
| Application | `know_ops_mcp/know_ops.py` | `KnowOps` 서비스 — knowledge ↔ storage 오케스트레이션 (CRUD/검색 유스케이스) |
| Domain | `know_ops_mcp/knowledge/` | `BaseKnowledge` + 서브타입 + 직렬화 |
| Infrastructure | `know_ops_mcp/storage/` | 파일 R/W 추상 + 백엔드 + 캐시 데코레이터 |
| Setup | `know_ops_mcp/setup/` | `know-ops-mcp setup` 마법사 + MCP 등록 스니펫 안내 (클라이언트 무관) |

## 프로젝트 구조

Flat layout. Application(`know_ops.py`)은 단일 모듈, 도메인(`knowledge/`)과 인프라(`storage/`)는 형제로 평탄화 (M15).

```
cursor-memo-re/                       ← 워크스페이스 / git repo (이름 유지)
├── know_ops_mcp/                     ← Python 패키지
│   ├── __init__.py
│   ├── server.py                     ← MCP Interface (FastMCP + bootstrap)
│   ├── know_ops.py                   ← Application (KnowOps 서비스 + 싱글턴)
│   ├── knowledge/                    ← Domain
│   │   ├── __init__.py               ← BaseKnowledge/GeneralKnowledge/register/for_type re-export
│   │   ├── base.py                   ← BaseKnowledge + 타입 레지스트리
│   │   ├── general.py                ← GeneralKnowledge (type="general")
│   │   └── serializer.py             ← 직렬화 유틸 (현재 구현: frontmatter+md)
│   ├── storage/                      ← Infrastructure
│   │   ├── __init__.py               ← StorageService + 싱글턴 + re-exports
│   │   ├── base.py                   ← BaseStorage ABC
│   │   ├── disk.py                   ← 디스크 R/W 헬퍼 (LocalDirectoryStorage + CachedStorage 공유)
│   │   ├── cache.py                  ← CachedStorage 데코레이터
│   │   └── backends/
│   │       ├── internal/             ← 외부 의존 X
│   │       │   ├── __init__.py       ← InternalStorage marker
│   │       │   ├── memory.py         ← MemoryStorage
│   │       │   └── local.py          ← LocalDirectoryStorage
│   │       └── external/             ← 외부 서비스
│   │           ├── __init__.py       ← ExternalStorage ABC (+ list_versions)
│   │           └── github.py         ← GitHubStorage (REST API)
│   └── setup/                        ← 사용자 인터페이스 (클라이언트 무관)
│       ├── cli.py                    ← typer app (serve/setup)
│       ├── wizard.py                 ← 대화형 마법사 + 진단 (재실행 시 read-only 모드)
│       └── config.py                 ← Config(toml) + load/save + to_storage_backend
├── pyproject.toml
├── README.md  CONTRIBUTING.md  AGENTS.md
└── docs/
    ├── ARCHITECTURE.md  (이 문서)
    ├── ROADMAP.md
    └── CHANGELOG.md
```

> 워크스페이스 디렉토리(`cursor-memo-re/`)와 GitHub repo 이름은 유지. Python 패키지 / dist / CLI / MCP 서버명은 모두 `know-ops-mcp`로 통일 (M14).

## 사이드이펙트 / 책임 경계 정책

- 자동화 범위는 **이 레포 자기 자신**에 한정 (M11).
  - 허용: `~/.config/know-ops-mcp/` (자체 설정), `~/.cache/know-ops-mcp/` (자체 캐시), 사용자가 명시적으로 지정한 storage 경로 / GitHub repo
  - 금지: 외부 도구의 설정 파일 (Cursor `~/.cursor/mcp.json`, Claude Desktop config 등) — 쓰기는 물론 **읽기도 X**
- 이 레포는 **MCP 서버**일 뿐 (M12). 누가 우리를 호출하는지(어떤 LLM 클라이언트인지)는 알 필요도, 알아서도 안 됨.
  - 설치/등록 확인은 각 클라이언트 책임
  - 본 도구는 MCP 표준 등록 스니펫만 제공 — wizard가 설치 출처에 맞춰 args 자동 조정 (M19)

## 배포 모델 — `uvx` 기반 install-less 실행 (M19)

- MCP 생태계 컨벤션(`uvx <pkg>` / `npx -y <pkg>`)을 따른다 — 사용자가 별도 install 단계 없이 mcp.json 한 번 작성하고 끝.
- 사용자 프리리퀴짓: `uv` 만 깔려 있으면 됨. `uvx`가 가상환경/의존성/Python 버전 모두 처리.
- 클라이언트(Cursor 등)가 `uvx know-ops-mcp` 를 stdio 로 spawn → MCP 서버 동작.
- 현재 PyPI 미배포 → `uvx --from git+<repo> know-ops-mcp` 로 동등 UX. PyPI 배포 후 `--from` 만 떼면 됨.
- wizard가 `direct_url.json` 으로 자기 설치 출처를 감지해 PyPI / git URL / local checkout 각각에 맞는 mcp.json 스니펫을 자동 생성.
- 나중에 원격 필요 시 transport만 `streamable-http`로 전환 가능 (코드 변경 없음).

---

## Interface — `know_ops_mcp/server.py`

FastMCP 3.2 기반 stdio MCP 서버. CLI에서 `know-ops-mcp serve`(또는 인자 없이 `know-ops-mcp`)로 실행, MCP 클라이언트가 subprocess로 자동 launch.

- 진입점: `know_ops_mcp/setup/cli.py:app` → `pyproject.toml` `[project.scripts]`
- 시작 시 `bootstrap()`이 user config을 로드해 storage 백엔드 적용. config 부재 시 `MemoryStorage` fallback + stderr 경고

### MCP Tools

| Tool | 파라미터 | 기능 |
| --- | --- | --- |
| `search_knowledge` | `query`, `tags?`, `limit?` | unique_name + title + description + content 대상 키워드 검색, 태그 필터 |
| `read_knowledge` | `unique_name` | unique_name으로 entry 전문 조회 |
| `write_knowledge` | `unique_name`, `title`, `description`, `content`, `tags?`, `type?` | entry 생성/수정 (Convention 검증) |
| `list_knowledge` | `tag?` | entry 목록 조회 (태그 필터) |
| `delete_knowledge` | `unique_name` | entry 삭제 |
| `refresh_knowledge_cache` | `unique_name?` | 로컬 캐시 무효화 (단건 / 전체). Cached backend 전용; 비캐시 backend에선 no-op |

---

## Application — `know_ops_mcp/know_ops.py`

CRUD/검색 유스케이스를 제공하는 단일 모듈. `KnowOps` 클래스 + 기본 싱글턴 `know_ops`.

- 메서드: `search`, `read`, `write`, `list_all`, `delete`, `refresh`
- `KnowOps(StorageService)` 의존성 주입 → 테스트 격리 가능 (M9)
- 메서드 이름은 클래스 컨텍스트 활용해 `_knowledge` 접미사 제거. MCP tool 이름은 외부 노출 API라 `*_knowledge` 그대로 유지

---

## Domain — `know_ops_mcp/knowledge/`

| 모듈 | 역할 |
| --- | --- |
| `__init__.py` | `BaseKnowledge`, `GeneralKnowledge`, `register`, `for_type` re-export |
| `base.py` | `BaseKnowledge` (공통 필드 + serialize/deserialize/summary + 타입 dispatch 레지스트리) |
| `general.py` | `GeneralKnowledge(BaseKnowledge)` (type="general") |
| `serializer.py` | 직렬화 유틸 (`serialize`, `deserialize`). 현재 구현: YAML frontmatter + md (M6) |

### 타입 시스템 (M5)

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

---

## Infrastructure — `know_ops_mcp/storage/`

ABC 기반 인터페이스 + 구현체 분리. `StorageService`가 단일 진입점, MCP 서버 부트스트랩에서 user config에 따라 backend 교체 (M8).

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

### 모듈

| 모듈 | 역할 |
| --- | --- |
| `base.py` | `BaseStorage` ABC (`read`, `write`, `delete`, `list_all`) |
| `__init__.py` | `StorageService` (backend 위임 + `configure` + `refresh`) + 기본 싱글턴 `storage` + 모든 backend re-export |
| `disk.py` | 디스크 R/W 헬퍼 (`ensure`/`read`/`write`/`delete`/`list_all`/`clear`). `LocalDirectoryStorage`와 `CachedStorage` 공유. write는 temp file + rename 원자성 (M18) |
| `cache.py` | `CachedStorage` 데코레이터 + `default_cache_dir()` (XDG_CACHE_HOME 존중) |
| `backends/internal/__init__.py` | `InternalStorage` marker (외부 의존 X 그룹) |
| `backends/internal/memory.py` | `MemoryStorage(InternalStorage)` |
| `backends/internal/local.py` | `LocalDirectoryStorage(InternalStorage)` — `disk.py` 헬퍼 사용 |
| `backends/external/__init__.py` | `ExternalStorage` ABC (+ abstract `list_versions`) |
| `backends/external/github.py` | `GitHubStorage` (httpx 기반 REST API, Trees listing, rate limit 1회 재시도) |

### LocalDirectoryStorage

- `LocalDirectoryStorage(path)` — `~` 확장 + 절대경로 정규화, 부재 시 디렉토리 자동 생성
- 파일 매핑: `unique_name` ↔ `<path>/<unique_name>.md`
- `default_data_dir()` — wizard가 default로 제안. `$XDG_DATA_HOME/know-ops-mcp`, env 부재 시 `~/.local/share/know-ops-mcp` (M17)
- 사용 시나리오: 단일 기기 prod

### GitHubStorage

- `GitHubStorage(repo_url, token, *, subdirectory="", branch="main")`
- Read/Write/Delete: GitHub REST Contents API (`GET/PUT/DELETE /repos/{owner}/{repo}/contents/<path>`)
- Listing: Git Trees API (`GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=true`). truncated 응답 시 `RuntimeError` raise (silent 누락 방지) (M16)
- 인증: PAT (`Authorization: Bearer <token>`)
- Rate limit: 429 또는 403 + `x-ratelimit-remaining=0` 시 `Retry-After` / `X-RateLimit-Reset` 따라 sleep, 1회 재시도 (60초 cap)
- `parse_repo_url(url) -> (owner, repo)` 헬퍼 — `https://github.com/owner/repo[.git]` 형식만 허용
- 단독 사용 가능하지만 매 호출 API 트래픽 발생. 일반적으로 `CachedStorage`로 wrapping

### CachedStorage (cache-on-read)

- `CachedStorage(backend: ExternalStorage, cache_dir)` — 어떤 `ExternalStorage`든 wrapping
- 캐시 위치: `cache_dir` 인자. 기본값 `default_cache_dir()` = `$XDG_CACHE_HOME/know-ops-mcp` 또는 `~/.cache/know-ops-mcp`
- 캐시 구조: `<cache_dir>/<unique_name>.md` 파일만 저장 (메타파일 X)
- TTL: 무한. 갱신은 명시적 `refresh(name=None)` 호출만

| 연산 | 동작 |
| --- | --- |
| `read(name)` | 캐시 hit → 그대로. miss → backend → 캐시 저장 |
| `list_all()` | `backend.list_versions()`로 이름 얻고 각 read() → 자연스럽게 캐시 활용 |
| `write(name, content)` | backend.write 후 캐시 즉시 갱신 (write-through, backend 실패 시 캐시 미오염) |
| `delete(name)` | backend.delete 후 캐시 evict |
| `refresh(name=None)` | 캐시 파일 제거. 다음 read 때 fetch |

설계 근거 + 검토한 대안: [`CHANGELOG.md`](CHANGELOG.md) M16.

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

### Storage 사용 시나리오

- 단일 기기 prod: `LocalDirectoryStorage(path)`
- 다기기 공유: `CachedStorage(GitHubStorage(repo_url, token, ...), cache_dir=...)`
- 기본 싱글턴은 `MemoryStorage()`, `bootstrap()`이 user config에 따라 `configure()` 호출
- `StorageService.refresh()`는 backend가 `refresh` 메서드를 가질 때만 위임 (Local/Memory에선 silent no-op)

---

## Setup CLI — `know_ops_mcp/setup/`

클라이언트-무관 사용자 인터페이스 (M12). 어떤 LLM 클라이언트를 쓰든 동일한 절차.

### 명령

| 명령 | 동작 |
| --- | --- |
| `know-ops-mcp` | 인자 없으면 `serve`와 동일 (클라이언트가 호출하는 형태) |
| `know-ops-mcp serve` | MCP 서버 실행 (stdio) |
| `know-ops-mcp setup` | 대화형 마법사. 재실행 시 현재 config + 스니펫만 보기도 가능 |

### 마법사 흐름

1. 기존 config 있으면 표시 후 "수정하시겠습니까?" 확인
   - **No** → 현재 config + MCP 등록 스니펫 출력 후 종료 (read-only 진단 경로) (M13)
   - **Yes** → 다음 단계
2. backend type 선택 (`local` / `github`)
3. backend별 추가 질문:
   - **local**: storage 경로 입력 (기본 `$XDG_DATA_HOME/know-ops-mcp`, 미설정 시 `~/.local/share/know-ops-mcp`) → `LocalDirectoryStorage` 인스턴스화로 검증
   - **github**: repo URL + token (token 비우면 `KNOW_OPS_MCP_GITHUB_TOKEN` env var 사용). branch/subdirectory는 기본값 (`main` / 루트). 변경 필요 시 `config.toml` 직접 편집
4. `~/.config/know-ops-mcp/config.toml`에 저장 (mode `0600`)
5. MCP 표준 등록 스니펫 출력 → 사용자가 자기 클라이언트의 설정 파일에 붙여넣음

### 모듈

| 모듈 | 역할 |
| --- | --- |
| `cli.py` | typer app — `serve` / `setup` |
| `wizard.py` | 대화형 흐름 (questionary) — backend 선택 → 분기 prompt → 진단 / 스니펫 출력 |
| `config.py` | `Config` Pydantic + discriminated union (`LocalStorageConfig` / `GitHubStorageConfig`) + TOML load/save (XDG, `chmod 0600`) + `to_storage_backend()` |

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

#### Token 우선순위 (GitHub backend 한정, M16)

1. `KNOW_OPS_MCP_GITHUB_TOKEN` 환경변수 (set 되어 있으면 무조건 우선)
2. `config.toml`의 `storage.token` 값
3. 둘 다 없으면 `RuntimeError` (명확한 안내 메시지)

### MCP 등록 스니펫 (M19)

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

`uvx`가 PATH에 없으면 마법사가 install 안내(`https://docs.astral.sh/uv/...`)를 출력. 자동 설치는 안 함 (외부 side-effect 정책, M11).

---

## Convention 요약

- Pydantic `BaseKnowledge` + 타입별 서브클래스 (`know_ops_mcp/knowledge/`)
- frontmatter 필드: `unique_name`, `type`, `title`, `description`, `tags`, `created`, `updated`
- `unique_name`: `^[a-z0-9-]+$` 강제 (LLM-사용자 합의)
- `description`: unique_name의 의미를 한 줄로 설명, 검색 대상 포함
- `type`: discriminator. 서브클래스가 `Literal[...]`로 자기 값 강제. 현재는 `GeneralKnowledge("general")` 단일

## Storage 선정 근거

- 원격 API 기반 온디맨드 접근 (전체 clone 불필요)
- `.md` 파일 그대로 저장, 브라우저에서 검수 가능
- Git 커밋 원자성, 버전 히스토리 무료
- PAT 인증, 크로스플랫폼, OS 무관
- 약점: 매 호출 API 트래픽 → `CachedStorage` 데코레이터로 완화 (M16)
