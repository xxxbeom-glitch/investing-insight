# TEST_RESULTS — M01 (in progress)

## Commands
```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe scripts\migrate.py
.\apps\api\.venv\Scripts\python.exe -m pytest tests\unit\test_ops_jobs.py tests\unit\test_production_readiness_check.py -q
.\apps\api\.venv\Scripts\python.exe scripts\run_daily_ingest.py --dry-run --limit 3
.\apps\api\.venv\Scripts\python.exe scripts\run_biweekly_research.py --dry-run --limit 1
.\apps\api\.venv\Scripts\python.exe scripts\backup_supabase_check.py
.\apps\api\.venv\Scripts\python.exe scripts\secret_scan.py
cd apps\web; npm run build
```

## Results
| Check | Result |
|-------|--------|
| migrate 0010 | PASS |
| unit tests (5) | PASS |
| daily dry-run | PASS |
| biweekly dry-run | PASS |
| backup_check (PITR pending) | FAIL expected (ok=false) |
| secret_scan | PASS |
| next build (+ /ops) | PASS |
| mvp tags | unchanged |

Evidence: dry-run job rows in `ops_jobs`; `evidence/backup_check.json`
