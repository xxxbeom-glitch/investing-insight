# TEST_RESULTS — M02

## Commands
```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe scripts\migrate.py
.\apps\api\.venv\Scripts\python.exe -m pytest tests\unit\test_topdown_engine.py tests\unit\test_ops_jobs.py -q
.\apps\api\.venv\Scripts\python.exe scripts\run_topdown_slice.py --dry-run
.\apps\api\.venv\Scripts\python.exe scripts\run_topdown_slice.py --skip-fred-fetch
.\apps\api\.venv\Scripts\python.exe scripts\secret_scan.py
```

## Results
| Check | Result |
|-------|--------|
| migrate 0011 | PASS |
| unit tests | PASS (9) |
| dry-run | PASS |
| live topdown (FRED ingest earlier + skip-fetch re-run) | PASS — regime=expansion, 3 industries QA PASS, 19 candidates, union 19 |
| secret_scan | PASS |
| tags | unchanged |

Live FRED ingest: 5 series, 2559 observations upserted (prior run in same session).
