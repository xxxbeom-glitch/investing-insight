# PLAN — Post-MVP 상태 이중 진단

- layer_id: status_diagnosis_ecb778e
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-11T14:30:00+00:00
- status: PASS (진단 산출물; 제품 GO 아님)
- previous_layer_commit: ecb778e
- head_at_start: ecb778e98d8f168b20594324e5b4bcf1ca819c42

## Goal

현재 제품 상태를 1차(구현 에이전트) + 2차(연결된 `research_qa_agent` LLM)로 독립 진단하고, 교차검증 보고서를 남긴다.

## In Scope

- HEAD / tag / GO / cron / hosting / Layer·Milestone 증거 수집
- 로컬 데모 리서치(AAPL) 실데이터 재조회 (secret 제외)
- `research_qa_agent` (`gpt-5.6-terra` / `reasoning.effort=high`) facts-only 호출
- `REPORT.md` 작성

## Out of Scope

- Post-MVP GO / tag
- cron enable
- 공개 호스팅
- Long-Term Optional
- production schema / M03–M06 의미 변경
- 외부 rereview bundle

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | `facts.json`에 secret 없이 상태 스냅샷이 있다 | yes |
| AC-2 | 2차 LLM 호출이 `llm_qa.json`에 model/response_id와 함께 기록된다 | yes |
| AC-3 | `REPORT.md`가 1차·2차·교차·다음 조치를 포함한다 | yes |
| AC-4 | GO/tag/cron을 켜지 않는다 | yes |

## Expected Files

- `facts.json`
- `live_snapshot.json`
- `llm_qa.json`
- `REPORT.md`
- `PLAN.md` / `IMPLEMENTATION.md` / `HANDOFF.md`

## Risks

- 2차 모델이 facts 밖을 발명하면 보고서가 오염됨 → schema 강제 + facts-only payload
- P0/P1 분류 체계가 Layer audit과 다를 수 있음 → 보고서에서 taxonomy를 명시
