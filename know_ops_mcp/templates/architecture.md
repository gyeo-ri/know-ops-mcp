# Template: architecture

- **key**: `projects/<project>/architecture`
- **tags**: `[<project>, architecture]` (+ tech tags)
- **description**: one line — the project's technical architecture

Body skeleton (everything below the line is the markdown body):

---
# <Project> 아키텍처

## 스택
- Frontend / Backend / Infra / Auth 등 레이어별 bullet

## 데이터 흐름
```
<요청 → 컴포넌트 → 저장소 흐름도>
```

## 저장소 / 데이터 모델
- DB 테이블, 버킷, 키 구조 등 (실제 코드 기준으로 정확히)

## 인증 / 권한
- 인증 방식, 보호되는 경로

## 배포
- 빌드/배포 명령, 주의점(gotcha)

## 주요 디렉토리
- 코드에서 자주 건드리는 위치
