# Features

구현 완료된 기능을 기록합니다.

## MCP Interface

FastMCP 3.2 기반 stdio MCP 서버. `cursor-memo` 명령으로 실행.

### MCP Tools

| Tool | 파라미터 | 기능 |
| --- | --- | --- |
| `search_notes` | `query`, `tags?`, `limit?` | 키워드 + 태그 기반 노트 검색 |
| `read_note` | `unique_name` | unique_name으로 노트 전문 조회 |
| `write_note` | `unique_name`, `title`, `content`, `tags?` | 노트 생성/수정 |
| `list_notes` | `tag?` | 노트 목록 조회 (태그 필터 가능) |
| `delete_note` | `unique_name` | 노트 삭제 |

### 현재 상태

- Knowledge Ops / Storage는 stub (인메모리 더미 데이터)
- 실제 GitHub Storage 연동은 미구현
