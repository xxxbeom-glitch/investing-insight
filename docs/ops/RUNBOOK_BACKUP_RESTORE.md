# Runbook — Supabase Backup / Restore

## Scope
Main SoR is **Supabase PostgreSQL**. Local Postgres is not SoR.

## Before Milestone 1 automation
1. In Supabase project: confirm **Backups / PITR** enabled for the production project used by `SUPABASE_DB_URL`.
2. Record project ref (hostname only) and backup retention in M1 evidence — **never** paste DB passwords.
3. Perform one restore drill to a disposable branch/DB (or document provider-supported restore steps).

## Backup (operator)
- Prefer Supabase managed backups/PITR over ad-hoc `pg_dump` for production.
- If emergency dump is required: run from a secured operator machine using `SUPABASE_DB_URL`; store dump outside git; encrypt at rest.

## Restore (operator)
1. Pause schedulers / writers (M1+).
2. Restore via Supabase dashboard or support-documented PITR to target timestamp.
3. Update connection string only if endpoint changes; rotate password if exposure suspected.
4. Run: `scripts/migrate.py` (idempotent), `scripts/production_readiness_check.py`, API `/health/db`.
5. Spot-check: latest `research_runs`, `snapshots` counts.

## Forbidden
- Committing dumps or connection strings
- Restoring over production without change window note in ops log
