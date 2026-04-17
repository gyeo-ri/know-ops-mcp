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
