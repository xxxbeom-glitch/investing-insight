# QA_REPORT

- layer_id: L00
- executed_at: 2026-08-10

## Acceptance Matrix

| Criterion | Evidence | Result |
|-----------|----------|--------|
| AC-1 API /health 200 | pytest `test_health_ok` | PASS |
| AC-2 web→api health | Next page fetches `/health*` · `npm run build` | PASS (runtime needs API up) |
| AC-3 api→Supabase | `/health/db` 503 placeholder host | FAIL |
| AC-4 migrations reproducible | `migrate.py --check` lists SQL; apply needs DB URL | PARTIAL |
| AC-5 secret git leakage 0 | `secret_scan.py` PASS | PASS |
| AC-6 secret not in web client | `check_client_secrets.py` PASS | PASS |
| AC-7 LLM profile validate | pytest + `/health/config` | PASS |
| AC-8 audit generator | pytest `test_generate_audit_layer` | PASS |

## Issues

| ID | Severity | Description | Root Cause | Status |
|----|----------|-------------|------------|--------|
| L00-001 | P1 | Supabase URL placeholder → DB health FAIL | `.env` host `xxxxx.supabase.co` | OPEN |
| L00-002 | P1 | SQL migrate apply 불가 | `SUPABASE_DB_URL` 없음 | OPEN |

## Final QA Status

- P0 Open: 0
- P1 Open: 2
- P2 Open: 0
- P3 Open: 0
- Blocking Status: FAIL
