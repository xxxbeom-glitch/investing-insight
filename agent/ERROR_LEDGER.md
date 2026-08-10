# Error Ledger

반복 가능성이 있거나 해결 과정이 다시 도움이 될 오류만 기록한다. 단순 오타와 일회성 오류는 기록하지 않는다.

## Active Errors

현재 등록된 오류 없음.

---

## Entry Template

### ERR-YYYYMMDD-001 — Short title

- Fingerprint: 핵심 오류 메시지 또는 안정적인 식별 문자열
- Status: OPEN | INVESTIGATING | BLOCKED | WORKAROUND | RESOLVED
- First seen: YYYY-MM-DD
- Last seen: YYYY-MM-DD
- Occurrences: 1
- Command: `실패한 명령`
- Affected area: 파일 또는 모듈
- Root cause: 확인된 경우에만 작성
- Fix: 적용한 최소 수정
- Verification: 해결을 확인한 명령과 결과
- Notes: 재발 방지에 필요한 내용

## Rules

- 실제 검증 성공 전에는 `RESOLVED`로 변경하지 않는다.
- 동일 Fingerprint는 새 항목을 만들지 말고 Occurrences를 증가시킨다.
