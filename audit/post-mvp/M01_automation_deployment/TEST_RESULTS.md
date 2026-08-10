# TEST_RESULTS — M01

- status: PASS
- completed_at: 2026-08-11

## Commands
```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe -m pytest tests\unit\test_ops_jobs.py -q
.\apps\api\.venv\Scripts\python.exe scripts\backup_free_plan.py readiness
.\apps\api\.venv\Scripts\python.exe scripts\backup_supabase_check.py
.\apps\api\.venv\Scripts\python.exe scripts\secret_scan.py
cd apps\web; npm run build
git rev-list -n 1 mvp-v0.1-pass
git rev-list -n 1 mvp-v0.1-review-pass
```

## Results
| Check | Result |
|-------|--------|
| unit tests | PASS |
| backup readiness (dump/verify/restore) | PASS |
| backup_supabase_check (backup_ready, scheduler false) | PASS |
| secret_scan | PASS |
| next build | PASS |
| mvp-v0.1-pass → e98ff33 | PASS |
| mvp-v0.1-review-pass → c1a6692 | PASS |

Evidence: `evidence/backup_readiness.json` (dump file itself gitignored under `storage/backups/`)
