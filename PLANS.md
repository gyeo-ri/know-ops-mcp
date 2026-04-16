# Plans

## 확정된 아키텍처

### 4개 구성요소

1. **MCP Interface**: tool을 MCP 프로토콜에 노출 (등록, 파라미터 스키마, 응답 포맷팅)
2. **Knowledge Ops**: tool이 무엇을 하는가 (CRUD + 검색 + Convention 검증). 요약은 LLM이, 검증/저장은 여기서
3. **Storage**: 파일 읽기/쓰기 추상 인터페이스. 1차 구현은 GitHub Private Repo (API)
4. **Setup CLI**: 설치 마법사(`cursor-memo setup`) + 배포(transport 결정) + LLM 클라이언트 자동 등록. 비개발자 대응

### 배포 방식: 로컬 설치형

- 각 기기에 CLI 도구로 설치 (`pip install` / `uv tool install`)
- Cursor가 로컬 프로세스로 실행 (stdio)
- FastAPI 등 별도 서버 래핑 불필요 (FastMCP가 HTTP transport 내장)
- 나중에 원격 필요 시 transport만 `streamable-http`로 전환 가능 (코드 변경 없음)

### Storage 선정: GitHub Private Repo

- 원격 API 기반 온디맨드 접근 (전체 clone 불필요)
- .md 파일 그대로 저장, 브라우저에서 검수 가능
- Git 커밋 원자성, 버전 히스토리 무료
- PAT 인증, 크로스플랫폼, OS 무관
- 약점: Search API 인덱싱 딜레이 (캐시로 완화 예정)

### Convention

- `unique_name` 기반 문서 식별 (LLM-사용자 합의)
- frontmatter: unique_name, tags, created, updated
- Knowledge Ops 레이어에서 검증

## 미결정 / 미구현 (TODO)

- [ ] 로컬 캐시 레이어 (읽기 성능 향상 + 오프라인 읽기 지원)
- [ ] Storage 구현체 추가 (S3, Flatnotes 등 교체 가능)
- [ ] Convention 규칙 고도화 (카테고리 체계, 자동 태깅)
- [ ] 사용자 인터페이스 상세 설계 (설치 마법사 UX)
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
