# Runbook — Supabase Backup / Restore (Free plan aware)

## Scope
Main SoR is **Supabase PostgreSQL**. Local Postgres is not SoR.

## Free plan (current lab)
Supabase **Free** does not include Automatic Backup / PITR.
**Do not** mark PITR as CONFIRMED.

Backup readiness (M01 AC-5) is satisfied only by:
1. Logical dump (`scripts/backup_free_plan.py dump` or `readiness`)
2. File verification (`verify`)
3. Restore drill into disposable schema + row-count match + schema drop
4. Audit evidence under `audit/post-mvp/M01_automation_deployment/evidence/backup_readiness.*`

```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe scripts\backup_free_plan.py readiness
.\apps\api\.venv\Scripts\python.exe scripts\backup_supabase_check.py
```

Dumps are written to `storage/backups/` (gitignored). Never commit dump files or DB URLs.

## Paid plan (future)
If Automatic Backup/PITR becomes available: document hostname + retention separately.
That does **not** auto-enable production schedulers without an explicit ops decision.

## Restore (disaster)
1. Keep production schedulers disabled until recovery complete.
2. Restore from latest verified dump (or provider PITR if available).
3. Run `scripts/migrate.py`, `scripts/production_readiness_check.py`, `/health/db`.
4. Spot-check: `research_runs`, `snapshots`, `securities` counts.

## Forbidden
- Fake `Status: CONFIRMED` for unavailable PITR
- Committing dumps or connection strings
- Restoring over production without a change note
