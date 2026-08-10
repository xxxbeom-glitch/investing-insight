# IMPLEMENTATION

- layer_id: L03
- status: PASS
- completed_at: 2026-08-10T20:38:51+09:00
- commit_hash: be7a006
- previous_layer_commit: fa541d2
- spec_version: investing-insight-spec-v1.6

## What Changed

- `SecClient` + `RateLimiter` (`apps/api/app/sec/client.py`)
- ticker→CIK map, companyfacts flatten with period_end vs published_at (`facts.py`)
- financial_facts immutable insert by `fact_id` (`ingest.py`)
- migration `0004_financial_facts.sql`

## Files Changed (from `git show --stat be7a006`)

- `apps/api/app/sec/__init__.py`, `client.py`, `facts.py`, `ingest.py`
- `migrations/0004_financial_facts.sql`
- `tests/integration/test_sec_ingest.py`, `tests/unit/test_sec.py`
- `audit/mvp/L03_sec_data/**`, `_docs/active-track.md`
- Totals: 15 files, +388 / −1

## Commands Run

```text
# recovered from TEST_RESULTS at PASS time
pytest tests -q   # 27 passed
# live AAPL companyfacts ingest (integration path)
```

Exact CLI cwd/venv invocation string: unknown — revalidated during L10 remediation  
Evidence: `audit/mvp/L10_mvp_freeze/evidence/pytest_revalidation_erp104.txt`

## Config / Schema Versions

- migration: `0004_financial_facts.sql`
- SEC policy: User-Agent required; ≤10 req/s (code-enforced)

## Deviations from PLAN

- none recorded in original audit stub
