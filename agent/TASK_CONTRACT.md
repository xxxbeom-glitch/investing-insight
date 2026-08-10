# Active Task Contract

이 문서는 현재 작업 한 건만 유지한다. 새 작업을 시작할 때 이전 내용을 교체한다.

## Task

- Task ID: RULES-001
- Screen ID: n/a
- Figma reference: n/a

## Goal

설계서 Loop/Audit에 맞게 Cursor 지침을 정리한다. L00 코드는 포함하지 않는다.

## Required

- 불필요 규칙 삭제
- product invariants · layer audit · git freeze 정렬
- audit 템플릿 · LAYER_CHECKLIST

## Allowed Scope

- `.cursor/rules/`, `agent/`, `audit/mvp/_templates/`, `_docs/`, `_logs/`, README(필요 시)

## Forbidden

- L00 앱 생성·dependency 설치
- 설계서 본문 임의 변경
- `.env` 커밋

## Verification

- [x] 규칙 파일이 설계서 게이트와 모순 없음 (문서 대조)
- [ ] L00 실행 (해당 없음)

## Done When

- 하네스 정리 커밋 완료

## Result

- DONE (커밋 후 갱신)
