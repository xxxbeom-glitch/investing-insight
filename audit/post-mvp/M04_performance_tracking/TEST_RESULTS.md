# TEST_RESULTS — M04

## Commands
```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe scripts\migrate.py
.\apps\api\.venv\Scripts\python.exe -m pytest tests\unit\test_performance_tracking.py -q
.\apps\api\.venv\Scripts\python.exe scripts\run_performance_eval.py
.\apps\api\.venv\Scripts\python.exe scripts\secret_scan.py
```

## Results
| Check | Result |
|-------|--------|
| migrate 0013 | PASS |
| unit tests | PASS |
| live eval on latest judgments | PASS (lab prices short → INCOMPLETE expected) |
| secret_scan | PASS |
| cron | disabled |
