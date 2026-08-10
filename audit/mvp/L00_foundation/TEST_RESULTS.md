# TEST_RESULTS

- layer_id: L00
- executed_at: 2026-08-10
- commit_hash: (see HANDOFF)

## Commands

```text
pytest tests -q
scripts/secret_scan.py
scripts/check_client_secrets.py
scripts/migrate.py
# /health /health/db /health/config via TestClient
```

## Results Summary

| Suite | Pass | Fail | Skip |
|-------|------|------|------|
| pytest | 7 | 0 | 0 |
| secret_scan | 1 | 0 | 0 |
| check_client_secrets | 1 | 0 | 0 |
| migrate apply + rerun idempotent | 1 | 0 | 0 |
| health/db table mode | 1 | 0 | 0 |

## Failures / Notes

- none (credentials fixed: real URL, pooler DB URL, valid secret)
