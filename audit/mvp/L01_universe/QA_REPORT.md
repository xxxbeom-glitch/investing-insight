# QA_REPORT

- layer_id: L01
- executed_at: 2026-08-10

## Acceptance Matrix

| Criterion | Evidence | Result |
|-----------|----------|--------|
| AC-1 NYSE/NASDAQ include | unit fixtures AAPL/IBM | PASS |
| AC-2 exclusion leakage 0 | unit excluded set | PASS |
| AC-3 ADR include | BABA ADRC | PASS |
| AC-4 duplicate identity 0 | unit stable ids + upsert | PASS |
| AC-5 exclusion_reason | unit + DB rows | PASS |
| AC-6 raw_hash | unit + sources table | PASS |
| AC-7 Massive live sample | integration ingest | PASS |

## Final QA Status

- P0 Open: 0
- P1 Open: 0
- Blocking Status: PASS
