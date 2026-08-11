# PLAN — 로컬 데모 리서치 (화면 결과물)

- track: post-mvp/phase-1
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-11T14:23:00+00:00
- status: PASS (local demo only; not product GO)
- previous_commit: 071e9ff
- scheduler_enable_allowed: false
- go_declared: false

## Goal

로컬에서 리서치 1회를 돌려 대시보드·후보 종목·종목 상세에 판단이 보이게 한다.  
명령·stdout·run_id를 audit에 남겨 나중에 검증 가능하게 한다.

## In Scope

- `scripts/run_biweekly_research.py --limit 5` (수동, cron 아님)
- 결과 JSON/HANDOFF를 `audit/post-mvp/local_demo_research_071e9ff/`에 기록
- TASK_CONTRACT · active-track 현황만 갱신

## Out of Scope

- production cron enable
- Post-MVP tag / GO
- hosted 공개 배포
- Long-Term Optional (타이밍·매매·증권사)

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | 새 `research_runs` row + `quant_scores` ≥ 1 | yes (API `/v1/dashboard`) |
| AC-2 | `/v1/runs/{run_id}/candidates`에 티커 ≥ 1 | yes |
| AC-3 | 해당 run에 judgment 또는 research_qa 기록 | yes |
| AC-4 | stdout/JSON에 secret 없음 · cron 그대로 DISABLED | yes |
| AC-5 | audit HANDOFF에 run_id · job_id · commands_run | yes |

## Expected Files

```
audit/post-mvp/local_demo_research_071e9ff/
├─ PLAN.md
├─ IMPLEMENTATION.md
├─ biweekly.json
├─ dashboard_after.json
├─ candidates.json
└─ HANDOFF.md
```

## Risks

- limit 5 종목에 재무가 없으면 quant shortlist 실패
- LLM unavailable → fail-closed (silent fallback 금지)

## Notes

사용자가 중간 GO를 위임. 봉인/스케줄러/배포 스위치는 켜지 않음.
