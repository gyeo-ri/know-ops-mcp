# History

프로젝트 주요 변경/마일스톤 기록. 시계열 (오래된 것부터 → 최신).

---

## M1. 아키텍처 기본 골격 확정

- 4개 구성요소 정의: **MCP Interface / Knowledge Ops / Storage / Setup CLI**
- 배포 방식: 로컬 설치형 (CLI 도구), Cursor가 stdio subprocess로 실행
- Storage 1차 후보: GitHub Private Repo (이식성 + 검수성 + 비용 0)
- 프로젝트 구조: flat layout (`src/` 없이 `cursor_memo/`를 루트에 직접 배치)

## M2. MCP 서버 기본 5개 tool 구현

- FastMCP 기반 stdio 서버 (`cursor_memo/server.py`)
- tool: `search/read/write/list/delete_*` 5종
- Convention: `unique_name` 정규식 강제(`^[a-z0-9-]+$`), frontmatter 필드 정형화

## M3. Storage 추상화 1차

- `BaseStorage` ABC (`read/write/delete/list_all`) 도입
- `MemoryStorage` 구현 (테스트/dev용, 인메모리 dict)
- 모듈 함수 facade로 default 인스턴스에 위임하는 패턴

## M4. Storage 백엔드 분류 체계 정리

- `backends/internal/` vs (향후) `backends/external/` 그룹 분리
- `InternalStorage` marker 클래스 도입 — 외부 의존 없는 backend 그룹 표지
- `LocalDirectoryStorage` 구현 — `~` 확장 + 디렉토리 자동 생성, `unique_name ↔ <path>/<name>.md` 매핑
- 사용 시나리오: 단일 기기 prod 또는 향후 ExternalStorage의 캐시

## M5. Knowledge 도메인 모델 추상화 (타입 시스템)

- 단일 `Note` Pydantic 모델 → `BaseNote` + 타입별 서브클래스(`GeneralNote`)로 리팩토링
- `@register` 데코레이터 + `for_type(type_str)` 레지스트리로 polymorphic dispatch
- `BaseNote.deserialize`가 frontmatter `type` 필드 보고 적절한 서브클래스 인스턴스화
- `summary()` 메서드로 LLM-친화 요약 직렬화

## M6. 직렬화 유틸 추상화

- `frontmatter.py` → `serializer.py`로 이름 변경 (라이브러리명 → 역할명)
- 함수 `dumps/loads` → `serialize/deserialize`로 정리
- 도메인 모델은 "(metadata dict, content str) ↔ str" 계약만 의존, 포맷(YAML+md)은 내부 구현으로 캡슐화

## M7. 패키지 개명 — `knowledge_ops` → `know_ops`

- 향후 프로젝트명 `KnowOpsMCP` 전환을 대비한 일관 개명
- 클래스/함수 동시 개명: `BaseNote → BaseKnowledge`, `GeneralNote → GeneralKnowledge`, `*_note → *_knowledge`
- 디렉토리 재배치: `models/` → `knowledge/`, top-level `storage/` → `know_ops/storage/`
- `know_ops`가 애플리케이션 레이어로서 도메인(`knowledge`)과 인프라(`storage`)를 자기완결로 포함

## M8. Storage 진입점 클래스화

- 모듈 함수 facade(`read/write/delete/list_all`) → `StorageService` 클래스 + 기본 싱글턴 `storage`
- `storage.configure(backend)`로 런타임 backend 교체 가능
- `BaseStorage`(계약) ↔ `StorageService`(애플리케이션 보유 단일 진입점) 역할 분리 명확화

## M9. KnowOps 서비스 클래스화

- CRUD 함수 묶음 → `KnowOps` 클래스로 캡슐화 + 기본 싱글턴 `know_ops`
- 생성자에 `StorageService` 주입 → 의존성 주입 / 테스트 격리 가능
- 메서드 이름은 클래스 컨텍스트 활용해 `_knowledge` 접미사 제거 (`search/read/write/list_all/delete`)
- MCP tool 이름은 외부 노출 API라 `*_knowledge` 그대로 유지

## M10. Setup CLI (1차)

- `cursor-memo setup` 대화형 마법사 (typer + questionary)
- CLI 진입점 단일화: `cursor-memo` → `serve`(default) / `setup` / `doctor` 서브커맨드
- 설정 파일: `~/.config/cursor-memo/config.toml` (XDG, 사람이 직접 편집 가능)
- 환경 자동 감지(`environment.detect`) + 지원 매트릭스 대조
- 서버 부트스트랩(`server.bootstrap`) — config 부재 시 Memory fallback + stderr 경고
- 지원 환경 매트릭스를 `setup/environment.py`에 데이터로 보유 → `cursor-memo doctor`로 노출 (md 문서 대신 서비스 내 표면화)

1차 마일스톤(macOS + Cursor + Local backend, 단일기기 prod) 완주 가능.

## M11. 외부 사이드이펙트 정책 확정

- 원칙: **이 레포가 자동화하는 범위는 자기 자신(`~/.config/cursor-memo/`)에 한정**. 외부 파일/환경(특히 Cursor의 `~/.cursor/mcp.json`)은 절대 수정하지 않음
- `~/.cursor/mcp.json` 자동 머지/백업 로직 제거 → 사용자에게 붙여넣을 JSON 스니펫과 파일 경로만 안내
- 이유: 한 번의 파싱 실패로 사용자의 다른 MCP 서버 설정이 유실될 위험 / 사용자 동의 없는 파일 수정 회피

## M12. 클라이언트 인식 통째 제거

- 원칙: 이 레포는 MCP 서버일 뿐, **누가 호출하는지 알 필요 없음**. 클라이언트 설치 여부 점검은 각 LLM 클라이언트 책임
- 제거: `cursor_memo/setup/clients/` 디렉토리 + `cursor_memo/setup/environment.py` 통째 (~210 LOC)
- 제거: 클라이언트 매트릭스, OS 감지, Cursor 설치 감지, `~/.cursor/mcp.json` read-only 점검까지 전부
- `wizard`: 환경 감지/분기 없이 storage 경로만 받고 → config 저장 → MCP 표준 스니펫 출력 → 끝
- `Config.path()` → `Config.location()` 개명 (storage path와 모호성 제거)
- `StorageConfig`: `backend: Literal["local","memory"]` + `LocalConfig` 래퍼 제거 → `path: str` 단일 필드
- `_dump_toml`/`_emit_table`/`_format_value` 일반 TOML serializer 30줄 → 우리 schema 1줄 하드코딩으로 대체

## M13. doctor 제거 + setup 일원화

- 매트릭스 사라진 시점부터 `doctor`가 하는 일 = config 표시 + 스니펫 출력 → `setup` 재실행으로 모두 가능
- `doctor.py` 삭제 + cli에서 doctor 커맨드 제거
- `setup` 재실행 시 "Modify? no" 답하면 현재 config + 스니펫 출력 (read-only 진단 경로)
- 사용자 명령은 `serve` / `setup` 둘만 남음 — 사람이 직접 쓰는 건 `setup` 하나
- `_validate_path`의 의미 없는 try/except 제거 (defensive over-engineering)
- 결과: setup 모듈 LOC 189 → 144 (시작점 377 대비 62% 감소)

## M14. 프로젝트 개명 — `cursor-memo` → `know-ops-mcp`

원래 PLANS.md에 예고되어 있던 개명을 GitHub repo / 워크스페이스 디렉토리만 남기고 일괄 적용.

- Python 패키지: `cursor_memo/` → `know_ops_mcp/`
- 모든 `from cursor_memo.X` import → `from know_ops_mcp.X`
- dist name (`pyproject.toml`): `cursor-memo` → `know-ops-mcp`
- CLI 바이너리: `cursor-memo` → `know-ops-mcp`
- MCP 서버명 (FastMCP init + 등록 스니펫 키): `cursor-memo` → `know-ops-mcp`
- XDG config 경로: `~/.config/cursor-memo/` → `~/.config/know-ops-mcp/`
- 기본 storage 경로: `~/Documents/cursor-memo` → `~/Documents/know-ops-mcp`
- **유지**: GitHub repo 이름, 워크스페이스 루트 디렉토리(`cursor-memo-re/`), 내부 `know_ops` 모듈명(M7 결정)
- 표기 컨벤션: snake_case = `know_ops_mcp`, kebab-case = `know-ops-mcp`, CamelCase brand = `KnowOpsMCP`
- 위 M1~M13 항목은 당시 시점 기록이므로 옛 이름을 그대로 둠

## M15. 패키지 레이아웃 평탄화 — `knowledge`/`storage`를 `know_ops` 밖으로

import 경로가 의존성 그래프와 어긋나 있던 문제를 해결.

- 증상: `setup`은 `know_ops` 오케스트레이터를 쓰지 않으면서 storage에 닿으려 `know_ops_mcp.know_ops.storage.backends.internal.local`까지 통과해야 했음. 디렉토리는 부모-자식, 실제 코드는 형제 의존성.
- 결정: 평탄화. `know_ops`(KnowOps 클래스)는 application service일 뿐 subsystem 컨테이너가 아님.
- 변경:
  - `know_ops_mcp/know_ops/knowledge/` → `know_ops_mcp/knowledge/`
  - `know_ops_mcp/know_ops/storage/` → `know_ops_mcp/storage/`
  - `know_ops_mcp/know_ops/__init__.py`(85 LOC 단일 파일) → `know_ops_mcp/know_ops.py` 모듈 (패키지로 둘 이유 없음)
  - 11개 `from know_ops_mcp.know_ops.X` import 일괄 치환
- 효과: setup의 storage import 한 단계 짧아짐, server.py 입장에서 `know_ops`/`storage`가 시각적으로도 형제로 보임, layer별 단위테스트 분리 용이

## M16. ExternalStorage + GitHub 백엔드 + Cache 레이어

1차 가치(1인 다기기 동기화)를 실현하기 위한 외부 저장소 통합. 단계적으로 청크 1~5에 걸쳐 진행하며, 본 항목은 설계 결정의 단일 출처.

### 배경
- LocalDirectoryStorage만으로는 다기기 동기화 불가. GitHub Repo가 1차 외부 백엔드 후보 (이식성/검수성/비용 0).
- 매 LLM 호출마다 GitHub API 직타하면 느리고 rate limit (인증 시 시간당 5000) 소진 위험. → 캐시 필요.

### 1. API mode
- **선택**: GitHub REST API + httpx, 파일 단위 I/O.
- 대안: git CLI subprocess (사용자 환경에 git 설치 강제), libgit2 바인딩 (의존성 무거움). 둘 다 기각.

### 2. Auth 전달 경로
- **선택**: PAT를 `config.toml`에 평문 저장 + `chmod 600`. `KNOW_OPS_MCP_GITHUB_TOKEN` 환경변수로 override 허용 (escape hatch).
- 검토 경로:
  - (a) `mcp.json`의 `env` 필드만 사용 — 사용자가 mcp.json 직접 편집해야 함. 다른 declarative config(repo URL, branch 등)는 setup wizard로 들어가는데 토큰만 따로 관리하는 분리가 어색.
  - (b) `config.toml` 단일화 — UX 우선. setup wizard가 모든 설정을 한 곳에서 처리. 평문 저장이 보안 trade-off지만 0600 + 사용자 home + scope 좁힌 PAT로 피해 한정.
- **결정**: (b). env override는 CI/스크립트용 escape hatch로 유지.

### 3. Cache TTL
- **선택**: 무한. 명시적 `refresh_knowledge_cache` MCP tool 호출로만 갱신.
- 이유: 시간 기반 TTL은 임의 stale window를 만들고, 사용자가 "지금 최신을 보고 싶다"는 의도를 표현할 방법이 없음. LLM 호출 흐름과 더 잘 맞는 건 명시적 refresh.

### 4. Listing 전략
- **선택**: Git Trees API (`recursive=true`). truncated 응답 시 `RuntimeError` raise (silent 누락 방지). 페이지네이션 안 함.
- 검토: GitHub Contents API의 디렉토리 listing은 1000 entry 한도 (페이지네이션 없음). Trees API는 ~100k entry / 7MB까지 단일 호출.
- 100k 초과는 repo 분할로 해결 권장. 임의 페이지네이션 구현은 over-engineering.

### 5. Rate limit 대응
- **선택**: 429 또는 403 + `x-ratelimit-remaining=0` 감지 시 `Retry-After`/`X-RateLimit-Reset` 헤더 따라 sleep, **1회만 재시도** (60초 cap). 진짜 auth fail (403 with remaining>0)은 재시도 안 함.
- 이유: 무한 재시도는 LLM 호출 hang 유발. 1회 한정으로 일시적 burst만 흡수.

### 6. Cache 구조 — Decorator 패턴
- **선택**: `CachedStorage(BaseStorage)`가 `ExternalStorage`를 wrapping하는 데코레이터.
- 검토: `LocalDirectoryStorage`에 cache 옵션을 내장하는 안 → 캐시 정책과 백엔드 종류는 직교 관심사. 단일 책임 위배.
- `ExternalStorage` ABC에 `list_versions() -> dict[str, str]` 추가 (name → opaque version, GitHub은 blob sha). 향후 다른 외부 백엔드에서 staleness 비교 등에 활용 가능한 계약.
- `LocalDirectoryStorage`는 캐싱 안 함 (이미 로컬 디스크).

### 7. Cache 위치
- **선택**: `~/.cache/know-ops-mcp/` (XDG_CACHE_HOME 존중). 단일 디렉토리.
- 가정: 1 사용자 = 1 backend. 멀티 backend 사용 사례가 실제로 나오면 그때 분리.

### 8. Cache 정책 — cache-on-read
가장 길게 검토된 결정. 핵심 질문: "list_all과 캐시는 어떻게 상호작용?"

**결정한 정책**:
| 연산 | 동작 |
| --- | --- |
| `read(name)` | 캐시 hit이면 그대로, miss면 backend → 캐시 저장 |
| `list_versions()` | 항상 backend 직행. entry 누락 방지 + refresh 판단 기준 |
| `list_all()` | `list_versions`로 이름 목록 얻고 → 각 이름 `read()` → 자연스럽게 캐시 활용 |
| `write(name, content)` | backend.write → 캐시도 즉시 갱신 (write-through) |
| `delete(name)` | backend.delete → 캐시 파일 evict |
| `refresh(name=None)` | 캐시 파일 제거 (전체 / 단건). 다음 read에서 backend fetch |

**검토한 대안**:
- (a) **list 결과까지 캐시**: 새 entry가 remote에 추가돼도 다음 refresh까지 안 보임 → 사용자 부담. 기각.
- (b) **write 시 캐시 invalidate**: 다음 read에서 fetch → 방금 write한 흐름에서 1번 미스 발생. write-through가 더 자연스러움.
- (c) **sha 기반 staleness 체크 매 read**: 매 read마다 list_versions 호출 → 캐시 의미 반감, 무한 TTL과 모순.
- (d) **캐시에 메타파일 `.shas.json`**: sha 비교 안 하니 불필요. 단순 `<name>.md` 파일 모음으로 충분.

**자연스러운 결과**:
- 첫 search/list_all = 1 tree call + N reads (N = entry 수). 이후 read만 하면 캐시 hit.
- 새 remote entry는 list_versions가 즉시 반영 → LLM 검색 결과에 노출됨 (콘텐츠는 그 시점에 fetch).
- 진짜 staleness는 "캐시된 콘텐츠가 remote에서 변경됐을 때"에 한정. manual `refresh(name)`로 해결.

**인정한 trade-off**:
- 다른 기기에서 같은 entry 수정 → 이 기기에서 read하면 stale 캐시. 사용자가 `refresh` 호출.
- 첫 search/list_all 비용이 큼. 이건 무한 TTL의 본질적 비용 — 이후 모든 호출이 거의 무료라는 것과 trade.

### 9. 청크 분할
사용자 검토/승인 cycle을 짧게 가져가기 위해 5 + docs 청크로 분할.
- C1 ✅ `storage/disk.py` 공유 헬퍼 + `LocalDirectoryStorage` 리팩터
- C2 ✅ `httpx` + `ExternalStorage` ABC + `GitHubStorage`
- C3 ⏳ `CachedStorage` 데코레이터
- C4 ⏳ `setup` config + wizard에 GitHub 분기
- C5 ⏳ `refresh_knowledge_cache` MCP tool
- C6 ⏳ docs (README/PLANS/FEATURES) 갱신

## M17. local backend default를 XDG_DATA_HOME 기반으로

기본 storage 경로를 `~/Documents/know-ops-mcp` → `$XDG_DATA_HOME/know-ops-mcp` (env 부재 시 `~/.local/share/know-ops-mcp`)로 변경.

- 이유:
  - `~/Documents`는 사용자가 만든 문서를 두는 영역. 앱이 자기 데이터를 default로 dump하는 관습 위반.
  - 우리는 이미 config(`~/.config/`), cache(`~/.cache/`)를 XDG 기반으로 두고 있음. data만 비표준이면 일관성 깨짐.
  - Linux에서 `~/Documents` 자체가 부재하거나 로케일에 따라 다른 이름일 수 있음 (영문 하드코딩의 함정).
- 검토한 대안:
  - `~/Documents/<app>` 유지 — 발견성 우선. Obsidian/Logseq 선례. 기각: 우리는 다기기(GitHub) 시나리오가 1차 가치라 발견성 비중 작음.
  - `~/.<app>/` 홈 직속 dotfile — 단순하지만 구식. 기각.
  - default 없음(필수 입력) — 첫 setup UX 마찰. 기각.
  - `platformdirs` 라이브러리 — 진짜 크로스플랫폼이지만 의존성 +1. 1차 타겟이 macOS/Linux라 과함.
- 인정한 trade-off: `~/Documents` 대비 발견성 ↓. 완화책:
  - setup wizard가 default 경로를 prompt에 노출 → 사용자가 그 자리에서 변경 가능.
  - README/FEATURES에 default 위치 명시.
- 변경:
  - `know_ops_mcp/storage/backends/internal/local.py`에 `default_data_dir()` 추가 (XDG_DATA_HOME 존중, `default_cache_dir`과 대칭).
  - `know_ops_mcp/storage/__init__.py`에서 re-export.
  - `setup/wizard.py`의 `DEFAULT_LOCAL_PATH` 상수 제거 → `default_data_dir()` 호출.
  - README/FEATURES의 default 경로 표기 갱신.

## M19. 배포/실행 모델 — `uvx` 채택, wizard 출처 자동 감지

배포 프리폴 모델로 `uvx <package>` 패턴 채택. wizard가 `_print_snippet()`에서 PEP 610 `direct_url.json`을 읽어 PyPI / git URL / local path를 구분하고 각각에 맞는 `command/args` 스니펫을 자동 생성.

- 동기: 첫 실 검증 시 `mcp.json: {"command": "know-ops-mcp"}` 가 `spawn ENOENT` 로 실패. 원인은 Cursor가 띄우는 자식 프로세스 PATH에 venv bin이 없음. 사용자에게 절대경로를 손으로 적게 하는 건 UX 실패.
- 검토한 대안:
  - `uv tool install` 권장 — 일반 CLI 툴(ruff/black) 표준 패턴. PATH 등록은 깔끔하나 "사전 install 단계 필요"라는 마찰. MCP 서버 생태계는 install-less 패턴(`uvx`/`npx`)으로 수렴 중. 기각.
  - `uv run --directory <repo>` — 개발자 친화적이지만 절대경로 노출 + 일반 사용자에겐 의미 불명. 기각(개발자 옵션으로 README에만 언급).
  - Docker — 격리 강하지만 무거움. 기각.
- 채택한 패턴: `uvx <package>` (PyPI 배포 후) / `uvx --from git+<url> <package>` (현 시점, 미배포). MCP 공식 서버들(`mcp-server-fetch`, `mcp-server-time` 등)과 동일한 형태.
- wizard 자동화: 사용자가 어떻게 know-ops-mcp를 실행했는지에 따라 스니펫이 달라야 하는 부담을 wizard가 흡수.
  - PyPI 설치 (no `direct_url.json`) → `["know-ops-mcp"]`
  - git URL (`vcs_info`) → `["--from", "git+<url>@<commit>", "know-ops-mcp"]`
  - 로컬 체크아웃 (`dir_info`) → `["--from", "<absolute path>", "know-ops-mcp"]`
- 부재 감지: `shutil.which("uvx")`가 None이면 wizard 끝에 install 안내(`https://docs.astral.sh/uv/...`) 출력. 자동 설치는 안 함(외부 side-effect 정책).
- uv 의존성을 사용자가 닿는 모든 표면에 일관되게 안내:
  1. README Requirements 섹션 — macOS/Linux/Windows install 명령 인라인.
  2. CLI `--help` epilog — 권장 호출 + uv 미설치 시 install URL.
  3. Wizard 스니펫 출력 — `shutil.which` 체크 후 부재 시 명령 + URL 출력.
  - wizard 안의 체크는 사실상 "pip install로 들어왔지만 uv는 안 깐 사용자" 한정으로만 의미가 있음(uvx 통해 진입했다면 항상 PATH에 잡힘). 그래도 cheap defensive code로 유지.
- 보류: PyPI publish (별도 마일스톤). 그 전까지 README는 git URL 형태를 1차 안내로 노출.

## M18. 디스크 쓰기 원자성 — temp file + rename

`disk.write`를 단순 `Path.write_text`에서 `temp file → Path.replace` 패턴으로 전환.

- 동기: 프로세스 kill / 전원 차단 / 디스크 가득 참 등으로 write 도중 중단되면 `.md` 파일이 truncated된 상태로 남을 수 있음. frontmatter가 잘려 다음 read에서 deserialize 실패.
- 변경: `<name>.md.tmp`에 먼저 쓰고 `Path.replace(target)`. POSIX rename은 원자적, `Path.replace`는 Windows에서도 기존 파일 덮어쓰기 가능.
- 효과:
  - `LocalDirectoryStorage`와 `CachedStorage` 양쪽 자동 적용 (둘 다 `disk.write` 사용).
  - `*.md` glob은 `.tmp` 무시 → 잔여 임시 파일이 list/search 결과에 노출되지 않음.
  - 동일 이름의 다음 write가 `.tmp`를 재생성하며 자연 정리.
- 보류: fsync (full durability). 이 도구는 노트 저장이라 atomicity로 충분. 향후 transactional 요구 생기면 추가.


