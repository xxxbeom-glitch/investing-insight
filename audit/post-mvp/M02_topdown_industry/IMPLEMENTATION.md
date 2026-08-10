# IMPLEMENTATION — M02 Top-down Industry Engine

## Built
1. Config: `fred_series.v0.1.yaml`, `industry_rules.v0.1.yaml`, `value_chain.v0.1.yaml`
2. Migration `0011_topdown_fred.sql`
3. FRED adapter: `app/macro/fred_client.py`, `ingest.py`
4. Regime: `app/macro/regime.py`
5. Top-down engine: assessments (6 dims), industry QA, value-chain snapshot, candidates, union
6. CLI: `scripts/run_topdown_slice.py`
7. API: `GET /v1/topdown/summary`
8. Unit tests: `tests/unit/test_topdown_engine.py`

## Constraints honored
- Production cron disabled
- FRED key fail-closed
- No API keys in stdout/evidence
