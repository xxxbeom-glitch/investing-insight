# PLAN

- layer_id: L05
- layer_name: snapshot_engine
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10T20:41:53+09:00 (after previous_layer_commit 929e49d)
- status: PASS (frozen)
- previous_layer_commit: 929e49d
- commit_hash: 4a9086e (PASS; HANDOFF hash recorded in f1a21d0)

## Goal

cutoff 당시 이용 가능 정보만 immutable snapshot으로 고정하고 content_hash·manifest schema로 역추적한다.

## In Scope

- research_runs / snapshots / snapshot_items (migration 0006)
- eligible_at / cutoff filter
- content_hash stability + reuse
- snapshot_manifest.schema.json validation
- integration tests

## Out of Scope

- Quant scoring (L06)
- LLM research
- Mutating past snapshots (forbidden)

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | cutoff 이후 records 0 | yes |
| AC-2 | same input/cutoff → same hash | yes |
| AC-3 | later restatement가 old snapshot 변경 0 | yes |
| AC-4 | source/version 역추적 | yes |
| AC-5 | manifest schema PASS | yes |

## Expected Files

- `apps/api/app/snapshot/engine.py`
- `migrations/0006_snapshots.sql`
- `packages/schemas/snapshot_manifest.schema.json`
- `tests/integration/test_snapshot.py`
- `audit/mvp/L05_snapshot_engine/**`

## Tests to Write First

- cutoff exclusion
- hash stability / reuse
- manifest required keys

## Risks

- Clock/timezone skew on cutoff comparisons
- Restatement after cutoff must not rewrite old snapshot

## Notes

- Recovered from git `4a9086e` + original QA stub + `07_MVP_LAYER_PLAN.md` L05.
