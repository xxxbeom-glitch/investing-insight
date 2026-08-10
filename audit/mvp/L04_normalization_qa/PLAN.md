# PLAN

- layer_id: L04
- layer_name: normalization_qa
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10T20:38:51+09:00 (after previous_layer_commit 154c19b)
- status: PASS (frozen)
- previous_layer_commit: 154c19b
- commit_hash: 6fbcff7 (PASS; HANDOFF hash recorded in 929e49d)

## Goal

공통 schema와 validated/quarantine 경계를 확립하고, validated layer에 QA FAIL 0을 보장한다.

## In Scope

- canonical validation helpers (`validate.py`)
- Data QA runner (`runner.py`)
- quarantine + data_quality_checks tables (migration 0005)
- unit/integration tests for missing≠zero, future dates, quarantine

## Out of Scope

- Snapshot cutoff engine (L05)
- Quant / LLM
- Provider ingest changes beyond QA hooks

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | unit fixture PASS | yes |
| AC-2 | missing ≠ zero | yes |
| AC-3 | invalid/future dates rejected | yes |
| AC-4 | quarantine traceable | yes |
| AC-5 | validated layer에 QA FAIL 0 | yes |

## Expected Files

- `apps/api/app/qa/**`
- `migrations/0005_data_qa.sql`
- `tests/unit/test_data_qa.py`, `tests/integration/test_data_qa_runner.py`
- `audit/mvp/L04_normalization_qa/**`

## Tests to Write First

- missing vs zero
- future date rejection
- quarantine insert + trace
- runner on DB sample → validated FAIL=0

## Risks

- Over-quarantine of valid ADR/foreign facts → tune fixtures carefully

## Notes

- Recovered from git `6fbcff7` + original stubs + `07_MVP_LAYER_PLAN.md` L04.
