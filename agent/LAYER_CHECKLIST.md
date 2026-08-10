# Layer Checklist

Layer를 시작·종료할 때 이 순서만 따른다. 상세 규칙: `.cursor/rules/25-layer-audit.mdc`

## Start

- [ ] `07_MVP_LAYER_PLAN.md`에서 해당 Layer Goal·Blocking Acceptance 확인
- [ ] 이전 Layer HANDOFF: PASS · P0=0 · P1=0 (L00 제외)
- [ ] `audit/mvp/LXX_name/` 생성
- [ ] `_templates/`에서 7파일 복사 (PLAN 먼저 채움)
- [ ] `agent/TASK_CONTRACT.md`를 이번 Layer로 교체
- [ ] `_docs/active-track.md` 현재 Layer 갱신

## Loop

- [ ] PLAN Acceptance가 테스트 가능한지 확인
- [ ] IMPLEMENT → TEST → QA
- [ ] FAIL 시 severity · root cause · fix · regression test · RETEST
- [ ] `OPEN_ISSUES` / `QA_REPORT` / `TEST_RESULTS` 갱신

## Freeze (PASS만)

- [ ] P0=0 · P1=0 · Blocking ALL PASS · evidence 있음
- [ ] tests 재실행
- [ ] audit 7파일 최신
- [ ] git commit → hash를 `HANDOFF.md`에 기록
- [ ] `active-track` · `TASK_CONTRACT` 정리
- [ ] 다음 Layer (또는 L10이면 MVP_HANDOFF + tag · **중단**)
