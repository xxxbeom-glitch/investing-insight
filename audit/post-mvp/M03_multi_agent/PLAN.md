# PLAN — Post-MVP Milestone 3 Multi-Agent Research

- milestone_id: M03
- spec: investing-insight-spec-v1.6 / 08_POST_MVP_ROADMAP.md Milestone 3
- branch: post-mvp/phase-1
- previous: M02 @ 94d38b2 / d118e40
- status: PASS
- constraints: production cron DISABLED; no free-conversation swarm; MVP baseline untouched

## Goal
Top-down/bottom-up 결과를 **공통 Snapshot**에 고정한 뒤, 역할별 Agent를 분리 실행한다.
동일 데이터 기준 · 구조화 JSON · Research QA + Adversarial Gate 통과 후에만 Final Selector.

## Roles (ordered)
1. Market
2. Industry
3. Company
4. Event
5. Research
6. Research QA Gate (blocking)
7. Adversarial Reviewer + Gate (blocking)
8. Final Selector

## In
- Snapshot binding + frozen topdown/bottom-up context
- Role-minimal JSON packets
- JSON Schema contracts per role
- llm-profile-v0.2 (multi-agent roles; terra only — luna/sol experiments out of scope)
- Orchestrator + mock client tests + optional live
- ops_jobs ledger; cron remains disabled

## Out
- Free-chat swarm
- Model optimization experiments (luna/sol) without benchmark approval
- Milestone 4 performance tracking
- Production scheduler enable

## Blocking Acceptance
| ID | Criterion | How to test |
|----|-----------|-------------|
| AC-1 | Binding freezes union/regime/assessments/bottom-up into immutable context + snapshot_id | unit/integration |
| AC-2 | All agent outputs share same snapshot_id/run_id | unit |
| AC-3 | Each role output validates against JSON schema; schema fail stops pipeline | unit |
| AC-4 | Research QA FAIL blocks adversarial + final | unit |
| AC-5 | Adversarial Gate FAIL blocks final selector | unit |
| AC-6 | No free-form chat API — only structured Responses path | code review + unit |
| AC-7 | P0=0 P1=0; cron disabled | OPEN_ISSUES + cron.examples |
| AC-8 | MVP tags untouched | git rev-list |

## Tests first
- `tests/unit/test_multi_agent.py`
