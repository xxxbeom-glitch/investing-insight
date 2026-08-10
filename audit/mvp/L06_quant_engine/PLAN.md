# PLAN

- layer_id: L06
- layer_name: quant_engine
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10T20:51:20+09:00 (after previous_layer_commit f1a21d0)
- status: PASS (frozen)
- previous_layer_commit: f1a21d0
- commit_hash: 7752b5e (PASS; HANDOFF hash recorded in 7f78093)

## Goal

LLM 없이 deterministic quant score·rank로 shortlist를 고정한다.

## In Scope

- metrics + component/total scores + ranks
- `config/quant_rules.v0.1.yaml` (versioned weights)
- migration `0007_quant_scores.sql`
- unit + integration determinism tests

## Out of Scope

- Research packet / LLM (L07+)
- Forced selection count
- Live trading signals

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | formula unit tests PASS | yes |
| AC-2 | same snapshot+rule → same score | yes |
| AC-3 | aggregation PASS | yes |
| AC-4 | LLM dependency 0 | yes |
| AC-5 | input_hash / rule_version 기록 | yes |

## Expected Files

- `apps/api/app/quant/**`
- `config/quant_rules.v0.1.yaml`
- `migrations/0007_quant_scores.sql`
- `tests/unit/test_quant.py`, `tests/integration/test_quant_engine.py`
- `audit/mvp/L06_quant_engine/**`

## Tests to Write First

- formula units
- deterministic scores for fixed snapshot
- rule_version persistence

## Risks

- Missing metrics → neutral handling must be deterministic
- Weight churn breaks experiment reproducibility → version pin

## Notes

- Recovered from git `7752b5e` + config + `07_MVP_LAYER_PLAN.md` L06.
