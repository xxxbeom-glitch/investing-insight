# PLAN — Post-MVP Milestone 6 V1→V2 Governance

- milestone_id: M06
- status: PASS
- constraints: do not auto-change rules from one failure; cron DISABLED

## Goal
score/prompt/model/profile 변경을 proposal → replay/holdout checklist → approval log → version freeze로 관리.

## Blocking Acceptance
| ID | Criterion | How to test |
|----|-----------|-------------|
| AC-1 | change_proposals table + statuses | migrate |
| AC-2 | create proposal with target artifact + rationale | CLI/unit |
| AC-3 | cannot approve without replay_notes + holdout_notes | unit |
| AC-4 | freeze records frozen_version | unit |
| AC-5 | single failure cannot auto-apply (no auto path) | code review |
| AC-6 | P0=0 P1=0; cron off | audit |
