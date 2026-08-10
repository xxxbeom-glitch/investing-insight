# PLAN

- layer_id: L02
- layer_name: market_data
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10
- status: IN_PROGRESS
- previous_layer_commit: bb1a54f

## Goal

일별 OHLCV를 Massive aggregates로 적재하고 QA·idempotency를 확보한다.

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | fixture OHLCV 파싱/검증 PASS |
| AC-2 | (security_id, trading_date) duplicate 0 on rerun |
| AC-3 | date/type/bounds QA FAIL → 적재 거부 |
| AC-4 | API failure silent success 0 |
| AC-5 | live sample AAPL daily bars ingest PASS |

## Out of Scope

- SEC (L03) · full-universe historical backfill automation
