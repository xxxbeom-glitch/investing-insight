# Active Task Contract

이 문서는 현재 작업 한 건만 유지한다. 새 작업을 시작할 때 이전 내용을 교체한다.

## Task

- Task ID: BOOTSTRAP-001
- Screen ID: n/a
- Figma reference: n/a

## Goal

markdown 라이브러리 지침 + 설계서 v1.5에 맞춘 저장소 골격·규칙을 준비한다. 런타임 앱은 만들지 않는다.

## Required

- web pack 규칙·로그·폰트·SECURITY
- 설계서 layout에 맞는 빈 디렉터리
- active-track / PROJECT_SPEC / decision-log 초기화

## Allowed Scope

- `.cursor/rules/`, `agent/`, `_docs/`, `_logs/`, 골격 폴더, README, `.gitignore`, `.env.example`

## Forbidden

- Next/FastAPI 앱 생성·dependency 설치 (합의·L00 전)
- 설계서 결정 임의 변경
- Post-MVP 범위 구현

## Verification

- [x] 폴더 트리·규칙 경로가 설계서와 모순 없음 (문서 기준)
- [ ] 앱 실행 (해당 없음)
- [ ] L00 Blocking QA (미착수)

## Done When

- 부트스트랩 커밋 가능 상태 · 설계서 기준 남은 논의 포인트가 사용자에게 전달됨

## Result

- DONE — 초기 커밋 `06604cd`
