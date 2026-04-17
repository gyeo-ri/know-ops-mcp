# AGENTS.md

LLM 챗봇용 공유 knowledge MCP 서버. Python + fastmcp. pre-PyPI, 단일 사용자 daily use.

## 다른 문서

- `README.md` — 사용자 진입점, 설치/실행 방법
- `CHANGELOG.md` — 모든 설계 결정의 근거 (M번호). 새 결정 전 관련 milestone 검색 권장
- `CONTRIBUTING.md` — 커밋/스타일 컨벤션
- `docs/ARCHITECTURE.md` — 현재 아키텍처 + 각 모듈 책임/계약
- `docs/ROADMAP.md` — 다음 작업 후보 (id별 status) + 검토 후 기각된 대안
- `tests/README.md` — 테스트 작성/실행

## 절대 규칙

- 외부 파일 자동 수정 금지 (`~/.cursor/mcp.json`, Claude Desktop config 등). 사용자에게 스니펫만 안내 (CHANGELOG M11)
- 클라이언트 환경 감지 코드 추가 금지 — 이 repo는 MCP 서버일 뿐 (CHANGELOG M12)
- 불필요한 주석 금지, 미래 예측 코드 금지

## 변경 후 의무

- 모듈/기능 추가·제거 → `docs/ARCHITECTURE.md` 갱신
- 설계 결정/trade-off → `CHANGELOG.md`에 milestone 추가 (`M<n>`)
- 로드맵 변경 → `docs/ROADMAP.md` 항목 status 업데이트 또는 추가
- 테스트 동반 (`tests/`)

## 작업 흐름

1. 큰 변경 전 `CHANGELOG.md`에서 관련 키워드 검색 — 같은 결정 재논의 회피
2. 작은 단위 커밋 (`CONTRIBUTING.md` 참고)
3. 사용자 승인 → 다음 단계
