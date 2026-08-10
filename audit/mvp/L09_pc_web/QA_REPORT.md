# QA_REPORT

- layer_id: L09
- executed_at: 2026-08-10
- commit_hash: eb2002c
- previous_layer_commit: cb6762a
- status: PASS
- spec_version: investing-insight-spec-v1.6

## Acceptance Matrix

| ID | Criterion | Evidence | Result |
|----|-----------|----------|--------|
| AC-1 | evidence navigation via company packet evidence | pages + reads API | PASS |
| AC-2 | latest vs historical via runs list/detail | runs pages | PASS |
| AC-3 | QA FAIL visible on dashboard/candidates/company | UI fields | PASS |
| AC-4 | 1280px+ shell (min-width) | Shell / globals CSS | PASS |
| AC-5 | LLM profile/model/effort on run detail + settings | settings + run pages | PASS |
| AC-6 | secret raw value exposure 0 | providers `*_set` only | PASS |

## Issue Counts

- P0 open: 0
- P1 open: 0
- P2 open: 1 (full browser e2e automation — backlog)
- P3 open: 0 (UI polish deferred to L10 P3 if any)

## Final QA Status

- Blocking Status: **PASS**
- Next layer eligible: yes (L10)
- Note: Full browser E2E automation remains P2; core acceptance via API + build + page implementation.
