# PLAN

- layer_id: L09
- layer_name: pc_web
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10T21:10:23+09:00 (after previous_layer_commit cb6762a)
- status: PASS (frozen)
- previous_layer_commit: cb6762a
- commit_hash: eb2002c (PASS; HANDOFF hash recorded in 3dfda44)

## Goal

PC Web only로 Dashboard → Runs → Candidates → Company → Evidence/Audit → Settings 탐색 경로를 연다.

## In Scope

- Read APIs (`apps/api/app/reads.py`) under `/v1/*`
- Next.js pages: home/dashboard, runs, run detail, candidates, company, audit, settings
- Shell with min-width 1280px
- Settings summary masks secrets; shows LLM profile/model/effort
- integration test for reads API + Next build

## Out of Scope

- Mobile/tablet QA
- Browser full E2E automation suite (P2 backlog)
- Post-MVP features
- Secret raw values in UI

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | evidence navigation works | yes |
| AC-2 | latest vs historical clear | yes |
| AC-3 | QA FAIL visible | yes |
| AC-4 | 1280px+ usable | yes |
| AC-5 | LLM profile/model/effort visible | yes |
| AC-6 | secret raw value exposure 0 | yes |

## Expected Files

- `apps/api/app/reads.py`, `main.py` route wiring
- `apps/web/src/app/**`, `components/Shell.tsx`, `lib/api.ts`
- `tests/integration/test_reads_api.py`
- `audit/mvp/L09_pc_web/**`

## Tests to Write First

- reads API integration
- Next production build
- settings providers `*_set` only (no raw secrets)

## Risks

- Browser E2E not automated → acceptance proven via API + build + page structure (full browser suite = P2)

## Notes

- Recovered from git `eb2002c` + original QA stub + `07_MVP_LAYER_PLAN.md` L09.
- Browser path revalidation during L10 remediation: see `audit/mvp/L10_mvp_freeze/evidence/web_server.log`, `api_server.log` (when remediation servers exercised).
