# TEST_RESULTS

- layer_id: L00
- executed_at: 2026-08-10

## Commands

```text
apps/api/.venv/Scripts/python.exe -m pytest tests -q
apps/api/.venv/Scripts/python.exe scripts/secret_scan.py
apps/api/.venv/Scripts/python.exe scripts/check_client_secrets.py
apps/api/.venv/Scripts/python.exe scripts/migrate.py --check
cd apps/web && npm run build
```

## Results Summary

| Suite | Pass | Fail | Skip |
|-------|------|------|------|
| unit+integration pytest | 7 | 0 | 0 |
| secret_scan | 1 | 0 | 0 |
| check_client_secrets | 1 | 0 | 0 |
| migrate --check | 1 | 0 | 0 |
| next build | 1 | 0 | 0 |
| health/db live | 0 | 1 | 0 |

## Failures / Notes

- `/health/db` → 503: DNS `xxxxx.supabase.co` Non-existent domain (placeholder URL)
- `migrate.py` apply exit 2: `SUPABASE_DB_URL` missing

## Evidence Paths

- pytest output in shell (7 passed)
- `apps/web` Next build success
