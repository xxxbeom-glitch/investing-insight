# TEST_RESULTS

- layer_id: L03
- executed_at: 2026-08-10T20:38:51+09:00 (PASS commit be7a006)
- commit_hash: be7a006
- spec_version: investing-insight-spec-v1.6

## Commands

```text
pytest tests -q
```

Exact interpreter path at historical PASS: unknown — revalidated during L10 remediation  
Revalidation: `audit/mvp/L10_mvp_freeze/evidence/pytest_revalidation_erp104.txt`

## Results Summary (historical, from original TEST_RESULTS)

| Suite | Pass | Fail | Skip | Source |
|-------|------|------|------|--------|
| pytest (full suite after L03) | 27 | 0 | 0 | original `TEST_RESULTS.md` @ be7a006 |
| Live AAPL companyfacts ingest | 1 | 0 | 0 | original `TEST_RESULTS.md` |

## Notes

- Historical per-test log files were not retained in audit at PASS time.
- Suite revalidation evidence attached under L10 remediation path above.
