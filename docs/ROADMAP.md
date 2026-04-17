---
purpose: 다음 작업 후보 + 검토 후 기각된 대안 (참고용)
audience: [humans, agents]
update_when: TODO 추가/완료/blocked, 새 대안 검토 후 기각, 결정이 milestone으로 굳을 때
---

# Roadmap

## 미결정 / 미구현 (TODO)

각 항목은 `id`로 참조 가능. status: `pending` (착수 대기) / `in-progress` / `blocked`.

| id | status | affects | description | refs |
| --- | --- | --- | --- | --- |
| pypi-publish | pending | `pyproject.toml` | PyPI 배포. 완료 시 wizard 스니펫이 `uvx know-ops-mcp` 단축형으로 자동 전환 | M19 |
| pytest-cov | pending | `tests/`, `pyproject.toml` | coverage 측정 도입. 임계치/CI gate 정책은 별도 결정 | M20 |
| new-knowledge-types | pending | `know_ops_mcp/knowledge/` | 새 Knowledge 타입 추가 (예: ConversationKnowledge, ProjectKnowledge). 추상화 완료, 실제 타입은 필요 시점에 | — |
| 100k-entry-repo | pending | `know_ops_mcp/storage/backends/external/github.py` | 100k entry 초과 repo 지원 (현재 Trees API truncated 응답에서 fail-fast) | M16 |
| cache-conflict | pending | `know_ops_mcp/storage/cache.py` | sha 기반 conflict 감지 검토. 현재 last-write-wins | M16 |
| remote-transport | pending | `know_ops_mcp/server.py` | streamable-http transport 전환 (원격 배포) | — |

## 검토 후 기각된 대안

같은 결정을 다시 논의하지 않기 위한 기록. 더 자세한 근거는 [`../CHANGELOG.md`](../CHANGELOG.md)의 해당 milestone 참조.

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
| 라이브 GitHub 테스트 (별도 슈트) | mock이 모든 분기 커버, 솔로 프로젝트라 CI 자동 검증 가치 ↓, main에 테스트 커밋 누적 부담 (M20) |
| `respx` (mock 라이브러리) | pytest 결합도 ↓. `pytest-httpx`가 fixture 자동 주입 + strict-by-default로 ergonomics 우위 (M20) |
