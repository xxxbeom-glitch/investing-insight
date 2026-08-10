# PLAN — Post-MVP Gate 0 Production Readiness Review

- gate_id: G00
- spec: investing-insight-spec-v1.6 / 08_POST_MVP_ROADMAP.md Gate 0
- branch: post-mvp/phase-1
- baseline: mvp-v0.1-review-pass @ c1a6692
- status: PASS

## Goal
MVP를 상시운영하기 전에 Production Readiness Review를 문서·스크립트·증거로 닫는다.
**Hosted deploy / cloud scheduler 구현은 Gate 0 범위가 아님** (Milestone 1).

## In
- Spec Gate 0 checklist topics
- Current local MVP stack (FastAPI, Next.js, Supabase PG, Massive/SEC/OpenAI)

## Out
- Public web deploy
- Daily/biweekly cloud schedulers
- FRED / top-down / multi-agent
- Changes to frozen MVP Layer audit PASS documents (L00–L10)

## Build
1. `docs/ops/PRODUCTION_READINESS.md` — topic-by-topic review (READY/GAP)
2. Runbooks: backup/restore, secret rotation, failure/quarantine, health monitoring
3. `scripts/production_readiness_check.py` — non-secret readiness probes + fail-closed reporting
4. Unit test for checker (no secret values in output)
5. `audit/post-mvp/G00_production_readiness/` 7-file audit

## Blocking Acceptance
| ID | Criterion | How to test |
|----|-----------|-------------|
| AC-1 | Gate 0 8 topics each have READY/GAP/N/A + evidence note | file review |
| AC-2 | Backup/restore runbook exists and names Supabase SoR | file exists |
| AC-3 | Secret rotation runbook exists; forbids git/UI exposure | file + checker |
| AC-4 | Readiness checker exits 0 on healthy local lab; prints no raw secrets | pytest + script |
| AC-5 | Explicit Milestone-1 GO/NO-GO recorded | QA_REPORT |
| AC-6 | P0=0 P1=0 | OPEN_ISSUES |
| AC-7 | MVP baseline tags untouched | `git rev-list` |

## Risks
- Treating Gate 0 as deploy work → scope creep into M1
- Writing secrets into runbooks → forbid; use variable names only

## Tests first
- `tests/unit/test_production_readiness_check.py`
