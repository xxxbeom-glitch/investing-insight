# Runbook — Health & Monitoring (local / pre-M1)

## Endpoints
- `GET /health` — process up
- `GET /health/db` — Supabase API credentials reach PostgREST
- `GET /health/config` — LLM profiles + config registry

## PC Web
- Dashboard / Audit / Settings show profile versions and provider `*_set` flags only.

## Local checks
```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe scripts\production_readiness_check.py
.\apps\api\.venv\Scripts\python.exe scripts\secret_scan.py
```

## M1 gap
External alerting (email/Slack/pager) and hosted uptime checks are Milestone 1 scope.
