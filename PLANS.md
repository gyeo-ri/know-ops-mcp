---
purpose: 아키텍처 결정의 현재 상태 + 다음 작업 후보
audience: [humans, agents]
update_when: 새 결정/기각/TODO 추가·완료 시
---

# Plans

## 확정된 아키텍처

### 구성요소

| 레이어 | 위치 | 역할 |
| --- | --- | --- |
| Interface | `know_ops_mcp/server.py` | MCP tool 노출 |
| Application | `know_ops_mcp/know_ops.py` | `KnowOps` 서비스 — knowledge ↔ storage 오케스트레이션 (CRUD/검색 유스케이스) |
| Domain | `know_ops_mcp/knowledge/` | `BaseKnowledge` + 서브타입 + 직렬화 |
| Infrastructure | `know_ops_mcp/storage/` | 파일 읽기/쓰기 추상 + 백엔드 + 캐시 데코레이터 |
| Setup | `know_ops_mcp/setup/` | `know-ops-mcp setup` 마법사 + MCP 등록 스니펫 안내 (클라이언트 무관) |

### 프로젝트 구조

Flat layout 채택. Application(`know_ops.py`)은 단일 모듈, 도메인(`knowledge/`)과 인프라(`storage/`)는 형제로 평탄화.

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
├── README.md  PLANS.md  FEATURES.md  HISTORY.md
```

> 워크스페이스 디렉토리(`cursor-memo-re/`)와 GitHub repo 이름은 유지. Python 패키지 / dist / CLI / MCP 서버명은 모두 `know-ops-mcp`로 통일.

### 배포 방식: `uvx` 기반 install-less 실행

- MCP 생태계 컨벤션(`uvx <pkg>` / `npx -y <pkg>`)을 따른다 — 사용자가 별도 install 단계 없이 mcp.json 한 번 작성하고 끝.
- 사용자 프리리퀴짓: `uv` 만 깔려 있으면 됨. `uvx`가 가상환경/의존성/Python 버전 모두 처리.
- 클라이언트(Cursor 등)가 `uvx know-ops-mcp` 를 stdio 로 spawn → MCP 서버 동작.
- 현재 PyPI 미배포 → `uvx --from git+<repo> know-ops-mcp` 로 동등 UX. PyPI 배포 후 `--from` 만 떼면 됨.
- wizard가 `direct_url.json` 으로 자기 설치 출처를 감지해 PyPI / git URL / local checkout 각각에 맞는 mcp.json 스니펫을 자동 생성 (M19).
- FastAPI 등 별도 서버 래핑 불필요 (FastMCP가 HTTP transport 내장).
- 나중에 원격 필요 시 transport만 `streamable-http`로 전환 가능 (코드 변경 없음).

### Storage 선정: GitHub Private Repo (다기기 시나리오)

- 원격 API 기반 온디맨드 접근 (전체 clone 불필요)
- `.md` 파일 그대로 저장, 브라우저에서 검수 가능
- Git 커밋 원자성, 버전 히스토리 무료
- PAT 인증, 크로스플랫폼, OS 무관
- 약점: 매 호출 API 트래픽 → `CachedStorage` 데코레이터로 완화 (M16 참조)

### Convention

- Pydantic `BaseKnowledge` + 타입별 서브클래스 (`know_ops_mcp/knowledge/`)
- frontmatter 필드: `unique_name`, `type`, `title`, `description`, `tags`, `created`, `updated`
- `unique_name`: `^[a-z0-9-]+$` 강제 (LLM-사용자 합의)
- `description`: unique_name의 의미를 한 줄로 설명, 검색 대상 포함
- `type`: discriminator. 서브클래스가 `Literal[...]`로 자기 값 강제. 현재는 `GeneralKnowledge("general")` 단일

## 사이드이펙트 / 책임 경계 정책

- 자동화 범위는 **이 레포 자기 자신**에 한정한다.
  - 허용: `~/.config/know-ops-mcp/` (자체 설정), `~/.cache/know-ops-mcp/` (자체 캐시), 사용자가 명시적으로 지정한 storage 경로 / GitHub repo
  - 금지: 외부 도구의 설정 파일 (Cursor `~/.cursor/mcp.json`, Claude Desktop config 등) — 쓰기는 물론 **읽기도 X**
- 이 레포는 **MCP 서버**일 뿐이다. 누가 우리를 호출하는지(어떤 LLM 클라이언트인지)는 알 필요도, 알아서도 안 된다.
  - 설치/등록 확인은 각 클라이언트 책임
  - 본 도구는 MCP 표준 등록 스니펫만 제공 (`{"mcpServers": {"know-ops-mcp": {"command": "uvx", "args": ["know-ops-mcp"]}}}` 형태; wizard가 설치 출처에 맞춰 args 자동 조정)
- 이유: 책임 경계 명확 / 외부 스키마 변경에 영향 받지 않음 / 사용자 다른 MCP 설정 유실 위험 0

## Storage 클래스 계층

```
BaseStorage (ABC)                        read/write/delete/list_all
├── InternalStorage (marker)             외부 의존 X
│   ├── MemoryStorage                    완료
│   └── LocalDirectoryStorage            완료
├── ExternalStorage (ABC)                + list_versions
│   └── GitHubStorage                    완료 (REST API + Trees listing)
└── CachedStorage                        완료 (ExternalStorage 데코레이터)
```

사용 시나리오:
- 단일 기기 prod: `LocalDirectoryStorage(path)`
- 다기기 공유: `CachedStorage(GitHubStorage(repo_url, token, ...), cache_dir=...)`

설계 결정/근거의 단일 출처: [HISTORY.md M16](HISTORY.md).

## 미결정 / 미구현 (TODO)

- [ ] 새 Knowledge 타입 추가 (예: ConversationKnowledge, ProjectKnowledge) — 추상화는 완료, 실제 타입은 필요 시점에
- [ ] PyPI publish — 마치면 wizard 스니펫이 자동으로 `uvx know-ops-mcp` 형태로 단축됨 (M19)
- [ ] 테스트 코드 (pytest 도입)
- [ ] coverage 측정 (`pytest-cov`) — 테스트가 충분히 쌓인 시점(T2 이후쯤)에 약점 가시화 용도. 임계치/CI gate는 별도 결정.
- [ ] 100k entry 초과 repo 지원 (현재는 Trees API truncated 응답에서 fail-fast)
- [ ] 캐시 conflict 처리 — 현재 last-write-wins. 충돌 빈발 시 sha 비교 도입 검토
- [ ] 원격 배포 전환 (streamable-http transport)

## 검토 후 기각된 대안

| 대안 | 기각 이유 |
| --- | --- |
| Obsidian vault (로컬) | 전체 파일 로컬 동기화 필요, OS 종속성 |
| Cloudflare R2 | 검색 기능 없음 |
| Supabase (Postgres) | `.md`가 아닌 DB 레코드, 사람 검수 불편, 이식성 낮음 |
| Google Drive | OAuth 세팅 고통 |
| Notion | 독자 포맷 lock-in |
| markdown-vault-mcp (기존 솔루션) | Star 5, 실질 기여자 1명, 신뢰도 부족 |
| 원격 서버 배포 (1차) | Storage가 이미 GitHub API(원격)라 MCP까지 원격이면 이중 네트워크 의존 |
| FastAPI 래핑 | FastMCP가 HTTP transport 내장, 불필요한 레이어 |
| `src/` layout (`src/know_ops_mcp/`) | 이 프로젝트에서 editable install 상태라 보호 효과 없음, 불필요한 중첩 |
| `mcp.json` `env`만으로 GitHub 토큰 전달 | declarative config는 wizard, 토큰만 분리 운영 = UX 분열. `config.toml` 단일화 + env override (M16) |
| `LocalDirectoryStorage`에 cache 옵션 내장 | 캐시 정책 ⊥ 백엔드 종류. 데코레이터 분리가 단일 책임 (M16) |
| Cache TTL (시간 기반) | 임의 stale window, 사용자 의도 표현 불가. 무한 TTL + 명시적 refresh tool (M16) |
| Cache list 결과 저장 | 새 remote entry 발견까지 refresh 필요 → UX 부담. list는 항상 fresh, 콘텐츠만 캐시 (M16) |
| GitHub Contents API listing | 페이지네이션 불가 1000 entry 한도. Trees API로 ~100k 단일 호출 (M16) |
| `uv tool install` 권장 (글로벌 PATH 등록) | 일반 CLI 툴 표준이지만 MCP 서버 생태계는 install-less(`uvx`/`npx`)로 수렴. "사전 install 잊으면 ENOENT" 마찰을 없애는 쪽 채택 (M19) |
| `mcp.json` 에 venv 절대경로 직접 명시 | 사용자가 손으로 `.venv/bin/...` 적어야 함. UX 실패 (M19) |
