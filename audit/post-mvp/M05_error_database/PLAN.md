# PLAN — Post-MVP Milestone 5 Error Database

- milestone_id: M05
- previous: M04
- status: PASS
- constraints: cron DISABLED; MVP baseline untouched

## Goal
판단/리서치 오분류를 구조화 카탈로그로 저장한다 (spec taxonomy).

## Taxonomy (spec)
- growth_persistence_overestimate
- valuation_underweight
- cycle_misread
- moat_competitor_miss
- momentum_macro_event_miss
- data_error
- unforeseen_external_shock

## Blocking Acceptance
| ID | Criterion | How to test |
|----|-----------|-------------|
| AC-1 | error_events table + taxonomy constraint | migrate + unit |
| AC-2 | CLI/API can record error linked to judgment/run | unit/integration |
| AC-3 | Invalid taxonomy rejected | unit |
| AC-4 | List/filter by type | unit |
| AC-5 | P0=0 P1=0; cron off; tags untouched | audit |
