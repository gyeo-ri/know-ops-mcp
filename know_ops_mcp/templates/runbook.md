# Template: runbook

- **key**: `projects/<project>/<area>/<name>-sop` or `…/runbook`
- **tags**: `[<project>, runbook]`
- **description**: one line — what operation this runbook covers

Body skeleton (everything below the line is the markdown body). Never paste real
secrets — reference where they live (Secrets Manager, env var name), not values.

---
# <Operation> 런북

## 목적 / 언제 쓰나
이 절차를 실행하는 상황

## 사전 조건
- 필요한 권한, 도구, 접근

## 절차
1. 단계
2. 단계

## 검증
- 성공 여부 확인 방법

## 롤백 / 트러블슈팅
- 실패 시 대응
