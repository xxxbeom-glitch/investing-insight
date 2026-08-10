# PLAN

- layer_id: L03
- layer_name: sec_data
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10T20:36:42+09:00 (after previous_layer_commit fa541d2)
- status: PASS (frozen)
- previous_layer_commit: fa541d2
- commit_hash: be7a006 (PASS; HANDOFF hash recorded in 154c19b)

## Goal

CIK mapping + company facts/filing metadata를 SEC EDGAR/data.sec.gov에서 적재하고, User-Agent·≤10 req/s·fail-closed를 강제한다.

## In Scope

- SEC client + `SEC_USER_AGENT`
- ≤10 req/s rate limiter
- ticker→CIK mapping
- companyfacts flatten (period_end vs published_at)
- financial_facts immutable insert + source hash
- unit + live sample ingest tests

## Out of Scope

- Normalization/quarantine boundary (L04)
- Snapshot / Quant / LLM
- Full-universe SEC backfill automation

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | US issuer + ADR/foreign issuer fixtures | yes |
| AC-2 | period vs published_at 분리 | yes |
| AC-3 | restatement overwrite 0 (on conflict do nothing) | yes |
| AC-4 | stored facts source traceability | yes |
| AC-5 | User-Agent test PASS | yes |
| AC-6 | limiter test PASS (≤10 rps spacing) | yes |
| AC-7 | 403/429 silent success 0 | yes |

## Expected Files

- `apps/api/app/sec/**`
- `migrations/0004_financial_facts.sql`
- `tests/unit/test_sec.py`, `tests/integration/test_sec_ingest.py`
- `audit/mvp/L03_sec_data/**`

## Tests to Write First

- UA header present
- rate limiter spacing
- 403/429 fail-closed
- period_end vs published_at fixture
- live AAPL companyfacts when credentials present

## Risks

- SEC rate limit / 403 without proper User-Agent
- Large companyfacts payloads → lab truncation (P2)

## Notes

- Recovered from git `be7a006` + layer PLAN stubs + `07_MVP_LAYER_PLAN.md` L03 Blocking Acceptance.
