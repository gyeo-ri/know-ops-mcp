# Plans

## 확정된 아키텍처

### 구성요소

| 레이어 | 위치 | 역할 |
| --- | --- | --- |
| Interface | `know_ops_mcp/server.py` | MCP tool 노출 |
| Application | `know_ops_mcp/know_ops/` (지식 관리 시스템) | `KnowOps` 서비스 — knowledge ↔ storage 오케스트레이션 (CRUD/검색 유스케이스) |
| Domain | `know_ops_mcp/knowledge/` | `BaseKnowledge` + 서브타입 + 직렬화 |
| Infrastructure | `know_ops_mcp/storage/` | 파일 읽기/쓰기 추상 + 백엔드 |
| Setup | `know_ops_mcp/setup/` | `know-ops-mcp setup` 마법사 + MCP 등록 스니펫 안내 (클라이언트 무관) |

### 프로젝트 구조

Flat layout 채택. `know_ops`는 애플리케이션 자기완결 (도메인 + 인프라를 안에 포함).

```
cursor-memo-re/                  ← 워크스페이스 / git repo (이름 유지)
├── know_ops_mcp/                ← Python 패키지
│   ├── __init__.py
│   ├── server.py                ← MCP Interface (FastMCP + bootstrap)
│   ├── know_ops/                ← 지식 관리 시스템 (Application)
│   │   ├── __init__.py          ← KnowOps 서비스 + 싱글턴
│   │   ├── knowledge/           ← 도메인
│   │   │   ├── __init__.py      ← BaseKnowledge/GeneralKnowledge/register/for_type re-export
│   │   │   ├── base.py          ← BaseKnowledge + 타입 레지스트리
│   │   │   ├── general.py       ← GeneralKnowledge (type="general")
│   │   │   └── serializer.py    ← 직렬화 유틸 (현재 구현: frontmatter+md)
│   │   └── storage/             ← 인프라
│   │       ├── __init__.py      ← StorageService + 싱글턴
│   │       ├── base.py          ← BaseStorage ABC
│   │       └── backends/
│   │           ├── internal/    ← 외부 의존 없는 backend 그룹
│   │           │   ├── __init__.py  ← InternalStorage marker
│   │           │   ├── memory.py    ← MemoryStorage
│   │           │   └── local.py     ← LocalDirectoryStorage
│   │           └── external/    ← 외부 서비스 backend 그룹 (향후)
│   └── setup/                   ← 사용자 인터페이스 (클라이언트 무관)
│       ├── cli.py               ← typer app (serve/setup)
│       ├── wizard.py            ← 대화형 마법사 + 진단 (재실행 시 read-only 모드)
│       └── config.py            ← Config(toml) + load/save
├── pyproject.toml
├── README.md  PLANS.md  FEATURES.md  HISTORY.md
```

> 워크스페이스 디렉토리(`cursor-memo-re/`)와 GitHub repo 이름은 유지. Python 패키지 / dist / CLI / MCP 서버명은 모두 `know-ops-mcp`로 통일.

### 배포 방식: 로컬 설치형

- 각 기기에 CLI 도구로 설치 (`pip install know-ops-mcp` / `uv tool install know-ops-mcp`)
- MCP 클라이언트가 로컬 프로세스로 실행 (stdio)
- FastAPI 등 별도 서버 래핑 불필요 (FastMCP가 HTTP transport 내장)
- 나중에 원격 필요 시 transport만 `streamable-http`로 전환 가능 (코드 변경 없음)

### Storage 선정: GitHub Private Repo

- 원격 API 기반 온디맨드 접근 (전체 clone 불필요)
- .md 파일 그대로 저장, 브라우저에서 검수 가능
- Git 커밋 원자성, 버전 히스토리 무료
- PAT 인증, 크로스플랫폼, OS 무관
- 약점: Search API 인덱싱 딜레이 (캐시로 완화 예정)

### Convention

- Pydantic `BaseKnowledge` + 타입별 서브클래스 (`know_ops_mcp/knowledge/`)
- frontmatter 필드: `unique_name`, `type`, `title`, `description`, `tags`, `created`, `updated`
- `unique_name`: `^[a-z0-9-]+$` 강제 (LLM-사용자 합의)
- `description`: unique_name의 의미를 한 줄로 설명, 검색 대상 포함
- `type`: discriminator. 서브클래스가 `Literal[...]`로 자기 값 강제. 현재는 `GeneralKnowledge("general")` 단일

## 사이드이펙트 / 책임 경계 정책

- 자동화 범위는 **이 레포 자기 자신**에 한정한다.
  - 허용: `~/.config/know-ops-mcp/` (자체 설정), 사용자가 명시적으로 지정한 storage 경로 (예: `~/Documents/know-ops-mcp`)
  - 금지: 외부 도구의 설정 파일 (Cursor `~/.cursor/mcp.json`, Claude Desktop config 등) — 쓰기는 물론 **읽기도 X**
- 이 레포는 **MCP 서버**일 뿐이다. 누가 우리를 호출하는지(어떤 LLM 클라이언트인지)는 알 필요도, 알아서도 안 된다.
  - 설치/등록 확인은 각 클라이언트 책임
  - 본 도구는 MCP 표준 등록 스니펫만 제공 (`{"mcpServers": {"know-ops-mcp": {"command": "know-ops-mcp"}}}`)
- 이유: 책임 경계 명확 / 외부 스키마 변경에 영향 받지 않음 / 사용자 다른 MCP 설정 유실 위험 0

## Storage 로드맵

```
BaseStorage (ABC)
├── InternalStorage (marker)              외부 의존 X
│   ├── MemoryStorage                     완료
│   └── LocalDirectoryStorage             완료
└── ExternalStorage (ABC, 캐시 옵션)      다음 작업
    └── GitHubStorage                     1차 외부 구현
```

사용 시나리오:
- 단일 기기 prod: `LocalDirectoryStorage(path)`
- 다기기 공유: `GitHubStorage(repo, token, cache=LocalDirectoryStorage(...))`

## 미결정 / 미구현 (TODO)

- [ ] `ExternalStorage` 추상 + `GitHubStorage` 구현 (캐시 옵션 내장) — 1인 다기기 가치
- [ ] 새 Knowledge 타입 추가 (예: ConversationKnowledge, ProjectKnowledge) — 추상화는 완료, 실제 타입은 필요 시점에
- [ ] LocalDirectoryStorage 원자적 쓰기 (temp file + rename)
- [ ] 테스트 코드 (pytest 도입)
- [ ] Setup CLI 확장 필요 시점에 — 단, 클라이언트별 분기 코드는 정책상 X. 스니펫은 이미 MCP 표준이라 추가 작업 없음
- [ ] 원격 배포 전환 (streamable-http transport)

## 검토 후 기각된 대안

| 대안 | 기각 이유 |
| --- | --- |
| Obsidian vault (로컬) | 전체 파일 로컬 동기화 필요, OS 종속성 |
| Cloudflare R2 | 검색 기능 없음 |
| Supabase (Postgres) | .md가 아닌 DB 레코드, 사람 검수 불편, 이식성 낮음 |
| Google Drive | OAuth 세팅 고통 |
| Notion | 독자 포맷 lock-in |
| markdown-vault-mcp (기존 솔루션) | Star 5, 실질 기여자 1명, 신뢰도 부족 |
| 원격 서버 배포 (1차) | Storage가 이미 GitHub API(원격)라 MCP까지 원격이면 이중 네트워크 의존 |
| FastAPI 래핑 | FastMCP가 HTTP transport 내장, 불필요한 레이어 |
| src layout (`src/know_ops_mcp/`) | 이 프로젝트에서 editable install 상태라 보호 효과 없음, 불필요한 중첩 |
