# Supabase Backup Note (M01 AC-5) — Free plan

Status: PITR_UNAVAILABLE

## Facts
- Supabase plan: **Free**
- Automatic Backup / PITR: **not available**
- Do **not** set a fake `Status: CONFIRMED` for PITR

## Free-plan AC-5 path
Use dump → verify → restore-drill evidence instead:
- `scripts/backup_free_plan.py readiness`
- Evidence: `backup_readiness.md` / `backup_readiness.json`

## Scheduler
Production cron / Cloud Scheduler remain **DISABLED** even after backup_ready PASS.
